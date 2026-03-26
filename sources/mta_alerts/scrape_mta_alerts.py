#!/usr/bin/env python3
"""
Scrape MTA service alerts for Kensington-relevant trains (G, L, J, Z, R).

Usage:
    uv run scrape_mta_alerts.py              # Scrape all current alerts
    uv run scrape_mta_alerts.py --last-day   # Only last full day
    uv run scrape_mta_alerts.py --since 2026-03-20  # Alerts since date
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.alert_item import AlertItem

# Configure logging
LOG_FILE = Path(__file__).parent / "scrape_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SOURCE_NAME = "mta_alerts"
MTA_ALERTS_URL = "https://new.mta.info/schedules/alerts"
BASE_DIR = Path(__file__).parent
SCRAPE_ITEMS_DIR = BASE_DIR / "scrape_items"

# Trains relevant to Kensington (11218)
KENNSINGTON_TRAINS = ["G", "L", "J", "Z", "R", "B", "Q"]

# Kensington-related stations and areas
KENNSINGTON_LOCATIONS = [
    "church ave", "grand army plaza", "metropolitan ave", "norwich st",
    "greenpoint", "williamsburg", "14th street", "broadway-lafayette",
    "jamaica", "queens boulevard", "forest hills", "downtown brooklyn"
]


def is_kensington_relevant(alert: dict) -> bool:
    """Check if alert affects Kensington area."""
    text = (alert.get("title", "") + " " + alert.get("description", "")).lower()
    
    # Check for relevant trains
    has_train = any(f"{train} train" in text or f" {train}-" in text.lower() 
                    for train in KENNSINGTON_TRAINS)
    
    # Check for relevant locations
    has_location = any(loc in text for loc in KENNSINGTON_LOCATIONS)
    
    return has_train or has_location


def fetch_mta_alerts():
    """Fetch current MTA service alerts."""
    logger.info(f"Fetching MTA alerts from {MTA_ALERTS_URL}")
    
    try:
        response = requests.get(MTA_ALERTS_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find alert cards - MTA uses specific classes
        alerts = []
        alert_cards = soup.find_all("div", class_=["alert-card", "service-alert"])
        
        for card in alert_cards[:100]:  # Limit results
            try:
                title_elem = card.find(["h3", "h4", "span"], recursive=False)
                description_elem = card.find("p")
                
                if title_elem:
                    alert = {
                        "title": title_elem.get_text(strip=True),
                        "description": description_elem.get_text(strip=True) if description_elem else "",
                        "url": f"{MTA_ALERTS_URL}#alert-{len(alerts)}"
                    }
                    
                    # Filter for Kensington relevance
                    if is_kensington_relevant(alert):
                        alerts.append(alert)
            except Exception as e:
                logger.warning(f"Error parsing alert card: {e}")
        
        return alerts
    except Exception as e:
        logger.error(f"Error fetching MTA alerts: {e}")
        return []


def parse_alerts_to_items(alerts, scrape_date=None):
    """Convert raw alerts to AlertItem Pydantic models."""
    items = []
    
    for alert in alerts:
        try:
            item = AlertItem(
                id=f"mta_{alert['title'][:50].lower().replace(' ', '_')}",
                title=alert["title"],
                description=alert.get("description", ""),
                url=alert.get("url", ""),
                affected_lines=[],  # Parse from title if possible
                alert_type="service_change",  # Could be: delay, closure, service_change
                published_at=scrape_date or datetime.now(),
                source="MTA"
            )
            items.append(item)
        except Exception as e:
            logger.warning(f"Error creating AlertItem: {e}")
    
    return items


def save_items(items, date_str=None):
    """Save scraped alerts to date-organized folders."""
    if not items:
        logger.info("No items to save")
        return 0
    
    # Use provided date or today
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    day_dir = SCRAPE_ITEMS_DIR / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    
    # Save all items as a single JSON array for this day
    filepath = day_dir / f"{SOURCE_NAME}_{date_str}.json"
    
    with open(filepath, "w") as f:
        json.dump([item.model_dump() for item in items], f, indent=2, default=str)
    
    saved_count = len(items)
    logger.info(f"Saved {saved_count} alerts to {filepath}")
    return saved_count


def get_last_full_day() -> str:
    """Get date string for last full day (yesterday)."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape MTA service alerts for Kensington-relevant trains"
    )
    parser.add_argument(
        "--last-day",
        action="store_true",
        help="Only scrape last full day (12:01am EST → 11:59pm)"
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Scrape alerts since date (YYYY-MM-DD)"
    )
    args = parser.parse_args()
    
    logger.info(f"Starting {SOURCE_NAME} scraper")
    
    # Determine date for saving
    if args.last_day:
        date_str = get_last_full_day()
        logger.info(f"Scraping alerts for last full day: {date_str}")
    elif args.since:
        # For --since, we'd need to check historical data (not available via web)
        logger.warning("MTA doesn't provide historical alerts via web. Scraping current alerts.")
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Scraping current alerts for {date_str}")
    
    # Fetch alerts
    raw_alerts = fetch_mta_alerts()
    logger.info(f"Found {len(raw_alerts)} Kensington-relevant alerts")
    
    # Parse to items
    items = parse_alerts_to_items(raw_alerts, scrape_date=datetime.strptime(date_str, "%Y-%m-%d"))
    
    # Save items
    saved = save_items(items, date_str=date_str)
    logger.info(f"Scraping complete. Saved {saved} alerts.")


if __name__ == "__main__":
    main()
