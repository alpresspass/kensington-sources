#!/usr/bin/env python3
"""
MTA Alerts Scraper for Kensington Free Press.

Scrapes MTA service alerts and filters for routes relevant to Kensington:
- G train (primary)
- L train (secondary - connects to G at 14th St)
- B, Q trains (via G connection)
- Bus routes: B25, B46, B63, B67
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import argparse
import logging
import os
import sys
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.mta_alert import MTAAlert

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Routes relevant to Kensington area
KENSINGTON_RELEVANT_ROUTES = {
    'subway': ['G', 'L', 'B', 'Q', 'N', 'W', 'R'],
    'bus': ['B25', 'B46', 'B63', 'B67', 'B15', 'B8']
}

MTA_ALERTS_URL = "https://new.mta.info/schedules/service-alerts"


def parse_date_from_description(desc: str) -> datetime:
    """Try to extract a date from the alert description."""
    # Common patterns in MTA alerts
    patterns = [
        r'(\d{1,2}/\d{1,2})',  # MM/DD format
        r'([A-Z][a-z]+ \d{1,2})',  # Month DD format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, desc)
        if match:
            date_str = match.group(1)
            try:
                # Try parsing with current year
                return datetime.strptime(f"{datetime.now().year} {date_str}", "%Y %b %d")
            except ValueError:
                pass
    
    return None


def scrape_mta_alerts(start_date: datetime = None, end_date: datetime = None) -> list[MTAAlert]:
    """
    Scrape current MTA service alerts.
    
    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        
    Returns:
        List of MTAAlert objects for relevant routes
    """
    logger.info(f"Fetching MTA alerts from {MTA_ALERTS_URL}")
    
    try:
        response = requests.get(MTA_ALERTS_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch MTA alerts: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find alert containers - structure may vary
    alert_containers = soup.find_all('div', class_='alert-container') or \
                       soup.find_all('article') or \
                       soup.select('.service-alert, .alert-item')
    
    if not alert_containers:
        logger.warning("Could not find alert containers on page")
        return []
    
    alerts = []
    current_time = datetime.now(timezone.utc)
    
    for container in alert_containers:
        # Extract route information
        route_elem = container.find('span', class_='route') or \
                     container.find('h2') or \
                     container.find('strong')
        
        if not route_elem:
            continue
            
        route_text = route_elem.get_text(strip=True)
        
        # Determine mode and extract route name
        mode = 'subway'
        route_name = route_text
        
        if any(route in route_text.upper() for route in ['BUS', 'MTA BUS']):
            mode = 'bus'
        elif 'LIRR' in route_text.upper():
            mode = 'lirr'
        elif 'PATH' in route_text.upper():
            mode = 'path'
        
        # Check if this route is relevant to Kensington
        is_relevant = False
        if mode == 'subway':
            is_relevant = any(route in route_text for route in KENSINGTON_RELEVANT_ROUTES['subway'])
        elif mode == 'bus':
            is_relevant = any(route in route_text for route in KENSINGTON_RELEVANT_ROUTES['bus'])
        
        if not is_relevant:
            continue
        
        # Extract alert description
        desc_elem = container.find('p') or container.find('div', class_='description')
        description = desc_elem.get_text(strip=True) if desc_elem else route_text
        
        # Determine alert type based on keywords
        alert_type = 'service_change'
        desc_lower = description.lower()
        if 'delay' in desc_lower:
            alert_type = 'delay'
        elif 'construction' in desc_lower or 'track work' in desc_lower:
            alert_type = 'construction'
        elif 'weekend' in desc_lower:
            alert_type = 'weekend_service'
        
        # Create unique ID
        alert_id = f"mta_{mode}_{route_name.replace(' ', '_').lower()}_{current_time.strftime('%Y%m%d_%H%M%S')}"
        
        alert = MTAAlert(
            id=alert_id,
            title=f"{route_text}: {description[:100]}..." if len(description) > 100 else f"{route_text}: {description}",
            published_at=current_time,
            route=route_name,
            mode=mode,
            alert_type=alert_type,
            description=description,
            severity=None,
            start_time=parse_date_from_description(description),
            end_time=None
        )
        
        alerts.append(alert)
    
    logger.info(f"Found {len(alerts)} relevant MTA alerts")
    return alerts


def save_alerts_to_file(alerts: list[MTAAlert], date_str: str):
    """
    Save alerts to a JSON file organized by date.
    
    Args:
        alerts: List of MTAAlert objects
        date_str: Date string for folder organization (YYYY-MM-DD)
    """
    if not alerts:
        logger.info("No alerts to save")
        return
    
    # Create date directory
    scrape_items_dir = os.path.join(os.path.dirname(__file__), 'scrape_items')
    date_dir = os.path.join(scrape_items_dir, date_str)
    os.makedirs(date_dir, exist_ok=True)
    
    # Save alerts to JSON file
    output_file = os.path.join(date_dir, f"mta_alerts_{date_str}.json")
    
    import json
    with open(output_file, 'w') as f:
        json.dump([alert.model_dump() for alert in alerts], f, indent=2, default=str)
    
    logger.info(f"Saved {len(alerts)} alerts to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Scrape MTA service alerts')
    parser.add_argument('--last-day', action='store_true', help='Get alerts from last full day (12:01am-11:59pm)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    args = parser.parse_args()
    
    # Determine date range
    if args.last_day:
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=1, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    elif args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        # Default: current time
        start_date = None
        end_date = None
    
    # Log scrape start
    log_file = os.path.join(os.path.dirname(__file__), 'scrape_log.txt')
    with open(log_file, 'a') as f:
        f.write(f"Scrape started: {datetime.now(timezone.utc).isoformat()}\n")
    
    logger.info("Starting MTA alerts scrape...")
    
    # Scrape alerts
    alerts = scrape_mta_alerts(start_date, end_date)
    
    if not alerts:
        logger.info("No relevant alerts found")
        with open(log_file, 'a') as f:
            f.write(f"Scrape completed: {datetime.now(timezone.utc).isoformat()} - No alerts\n")
        return
    
    # Save to date-organized folder
    today_str = datetime.now().strftime('%Y-%m-%d')
    save_alerts_to_file(alerts, today_str)
    
    logger.info(f"Scraped {len(alerts)} MTA alerts")
    
    # Log scrape completion
    with open(log_file, 'a') as f:
        f.write(f"Scrape completed: {datetime.now(timezone.utc).isoformat} - {len(alerts)} alerts\n")


if __name__ == '__main__':
    main()
