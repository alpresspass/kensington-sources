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

# Add kensington-sources root to path for imports (parent of sources/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

# MTA GTFS-RT Alerts endpoint - provides real-time service alerts for all modes
MTA_ALERTS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fall-alerts.json"


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
    Scrape current MTA service alerts from GTFS-RT feeds.
    
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
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch MTA alerts: {e}")
        return []
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return []
    
    # GTFS-RT alerts come in a specific format
    # The response contains header and entity at top level (not nested under feed_message)
    if not isinstance(data, dict):
        logger.warning("Unexpected response format")
        return []
    
    alerts = []
    current_time = datetime.now(timezone.utc)
    
    # Extract entities directly from root level
    entities = data.get('entity', [])
    
    for entity in entities:
        if not isinstance(entity, dict):
            continue
            
        # Get the alert information from the entity
        alert_data = entity.get('alert', {})
        if not alert_data:
            continue
            
        # Extract affected routes/areas - GTFS-RT uses 'informed_entity' for alerts
        informed_entities = alert_data.get('informed_entity', [])
        route_names = []
        mode = 'subway'  # default
        
        for informed in informed_entities:
            if isinstance(informed, dict):
                agency_id = informed.get('agency_id', '')
                route_id = informed.get('route_id', '')
                trip_id = informed.get('trip_id', '')
                start_stop_id = informed.get('start_stop_id', '')
                end_stop_id = informed.get('end_stop_id', '')
                
                # Determine mode from agency ID
                if 'MTABC' in agency_id or 'NYCTBus' in agency_id:
                    mode = 'bus'
                elif 'LIRR' in agency_id:
                    mode = 'lirr'
                elif 'PATH' in agency_id:
                    mode = 'path'
                else:
                    mode = 'subway'
                
                # Extract route name from various fields
                if trip_id and not trip_id.startswith('0'):
                    route_names.append(trip_id)
                elif start_stop_id and '/' in str(start_stop_id):
                    route_names.append(str(start_stop_id).split('/')[0])
                elif end_stop_id and '/' in str(end_stop_id):
                    route_names.append(str(end_stop_id).split('/')[0])
                
                # Add route_id if present
                if route_id:
                    route_names.append(route_id)
        
        if not route_names:
            continue
            
        # Check if any route is relevant to Kensington
        is_relevant = False
        for route_name in route_names:
            if mode == 'subway' and any(route in str(route_name) for route in KENSINGTON_RELEVANT_ROUTES['subway']):
                is_relevant = True
                break
            elif mode == 'bus' and any(route in str(route_name) for route in KENSINGTON_RELEVANT_ROUTES['bus']):
                is_relevant = True
                break
        
        if not is_relevant:
            continue
            
        # Extract alert text/description
        # GTFS-RT alerts use header_text for the main message and info_text for details
        header_text_obj = alert_data.get('header_text', {})
        causality_info = alert_data.get('causality', [])
        info_text_list = alert_data.get('info_text', [])
        
        description_parts = []
        
        # Extract from header_text.translation[0].text (main alert message)
        if isinstance(header_text_obj, dict):
            translations = header_text_obj.get('translation', [])
            if isinstance(translations, list) and len(translations) > 0:
                main_text = translations[0].get('text', '') if isinstance(translations[0], dict) else ''
                if main_text:
                    description_parts.append(main_text)
        
        # Also check causality for additional context
        for item in (causality_info if isinstance(causality_info, list) else [causality_info]):
            if isinstance(item, dict):
                text = item.get('text', '')
                if text:
                    description_parts.append(text)
        
        # And info_text for details
        for item in (info_text_list if isinstance(info_text_list, list) else [info_text_list]):
            if isinstance(item, dict):
                text = item.get('text', '')
                if text:
                    description_parts.append(text)
        
        description = ' '.join(description_parts) if description_parts else f"Service alert for {', '.join(route_names)}"
        
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
        route_str = '_'.join(route_names[:2])  # Use first two routes for ID
        alert_id = f"mta_{mode}_{route_str.replace(' ', '_').lower()}_{current_time.strftime('%Y%m%d_%H%M%S')}"
        
        title = f"{', '.join(route_names)}: {description[:100]}..." if len(description) > 100 else f"{', '.join(route_names)}: {description}"
        
        alert = MTAAlert(
            id=alert_id,
            title=title,
            published_at=current_time,
            route=', '.join(route_names),
            mode=mode,
            alert_type=alert_type,
            description=description,
            severity=None,
            start_time=None,
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
