#!/usr/bin/env python3
"""
Scrape NY YIMBY RSS feed for NYC construction and development news.
NY YIMBY covers building projects, zoning changes, and real estate developments across NYC.
"""

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
from typing import Optional

try:
    from feedparser import parse as parse_rss
except ImportError:
    print("Error: feedparser not installed. Run: uv add feedparser")
    sys.exit(1)

# Add project root to path for imports (sources/nyyimby_rss/ -> sources/ -> kensington-sources/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models import RSSItem

SOURCE_NAME = "nyyimby_rss"
BASE_URL = "https://newyorkyimby.com/feed"
OUTPUT_DIR = Path(__file__).parent / "scrape_items"
LOG_FILE = Path(__file__).parent / "scrape_log.txt"

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape NY YIMBY RSS feed")
    parser.add_argument("--days-ago", type=int, default=1,
                       help="Number of days back to scrape (default: 1)")
    parser.add_argument("--start-date", type=str, default=None,
                       help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, default=None,
                       help="End date in YYYY-MM-DD format")
    return parser.parse_args()

def log_message(message: str):
    """Append a timestamped message to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def get_date_range(args):
    """Calculate start and end datetimes for scraping."""
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
        end = datetime.strptime(args.end_date, "%Y-%m-%d") + timedelta(days=1)
    else:
        # Default: last N full days (12:01 AM to 11:59 PM)
        now = datetime.now()
        end = now.replace(hour=23, minute=59, second=59)
        start = now - timedelta(days=args.days_ago)
        start = start.replace(hour=0, minute=1, second=0)
    
    return start, end

def scrape_nyyimby(start: datetime, end: datetime) -> list[RSSItem]:
    """
    Scrape NY YIMBY RSS feed for items within the date range.
    Returns a list of RSSItem objects.
    """
    log_message(f"Starting NY YIMBY scrape from {start} to {end}")
    
    # Parse RSS feed
    feed = parse_rss(BASE_URL)
    
    items = []
    for entry in feed.entries:
        # Parse publication date
        pub_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])
        
        # Skip if no date or outside range
        if not pub_date or pub_date < start or pub_date > end:
            continue
        
        # Create RSSItem
        item = RSSItem(
            id=f"{SOURCE_NAME}_{entry.get('link', '').replace('/', '_')}",
            title=entry.get('title', ''),
            published_at=pub_date,
            link=entry.get('link', ''),
            summary=entry.get('description', ''),
            author=entry.get('author', '')
        )
        items.append(item)
    
    log_message(f"Found {len(items)} NY YIMBY items")
    return items

def save_items(items: list[RSSItem]):
    """Save items to JSON files organized by date."""
    if not items:
        log_message("No items to save")
        return
    
    # Group items by date
    items_by_date = {}
    for item in items:
        date_str = item.published_at.strftime("%Y-%m-%d")
        if date_str not in items_by_date:
            items_by_date[date_str] = []
        items_by_date[date_str].append(item)
    
    # Save each day's items
    for date_str, day_items in sorted(items_by_date.items()):
        output_path = OUTPUT_DIR / date_str
        output_path.mkdir(parents=True, exist_ok=True)
        
        json_file = output_path / f"{SOURCE_NAME}_{date_str}.json"
        
        # Convert to serializable format - convert datetime to ISO string
        def serialize_item(item):
            d = item.model_dump()
            if 'published_at' in d and isinstance(d['published_at'], datetime):
                d['published_at'] = d['published_at'].isoformat()
            return d
        data = [serialize_item(item) for item in day_items]
        
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        log_message(f"Saved {len(day_items)} items to {json_file}")

def main():
    args = parse_args()
    start, end = get_date_range(args)
    
    items = scrape_nyyimby(start, end)
    save_items(items)
    
    log_message("NY YIMBY scrape complete")

if __name__ == "__main__":
    main()
