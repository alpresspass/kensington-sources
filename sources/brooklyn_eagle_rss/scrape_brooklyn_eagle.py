#!/usr/bin/env python3
"""
Scrape Brooklyn Eagle RSS feed for Kensington-relevant content.

Usage:
    uv run scrape_brooklyn_eagle.py              # Scrape all available content
    uv run scrape_brooklyn_eagle.py --last-day   # Only last full day (12:01am EST → 11:59pm)
    uv run scrape_brooklyn_eagle.py --since 2026-03-20  # Items since date
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import feedparser

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.rss_item import RSSArticleItem

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

SOURCE_NAME = "brooklyn_eagle_rss"
RSS_URL = "https://brooklyneagle.com/feed"
BASE_DIR = Path(__file__).parent
SCRAPE_ITEMS_DIR = BASE_DIR / "scrape_items"

# Kensington-related keywords for filtering
KENNSINGTON_KEYWORDS = [
    "kensington", "greenpoint", "williamsburg", "bed-stuy", "bedford-stuyvesant",
    "brooklyn heights", "downtown brooklyn", "fort greene", "boerum hill",
    "11218", "11222", "11249", "11205", "11206", "11201", "11217"
]


def is_kensington_relevant(item: RSSArticleItem) -> bool:
    """Check if RSS item is relevant to Kensington area."""
    text = (item.title + " " + (item.summary or "")).lower()
    return any(keyword in text for keyword in KENNSINGTON_KEYWORDS)


def parse_rss_feed():
    """Parse Brooklyn Eagle RSS feed and return items."""
    logger.info(f"Fetching RSS feed from {RSS_URL}")
    
    try:
        # Fetch raw content first for better control
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Accept': 'application/rss+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://brooklyneagle.com/',
        }
        resp = requests.get(RSS_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        
        # Clean up common XML issues in Brooklyn Eagle feed
        cleaned_content = resp.text
        # Fix unescaped ampersands in URLs and text
        cleaned_content = re.sub(r'(?<!&)&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', cleaned_content)
        
        feed = feedparser.parse(cleaned_content)
        
        items = []
        for entry in feed.entries[:50]:  # Limit to first 50 entries
            try:
                item = RSSArticleItem(
                    id=entry.get("id", entry.link)[:100],
                    title=entry.title,
                    link=entry.link,
                    summary=entry.get("summary", "")[:2000] if entry.get("summary") else None,
                    content=None,  # Full content not needed for headlines
                    published_at=datetime.fromisoformat(entry.published_parsed[:19].replace(" ", "T"))
                        if hasattr(entry, 'published_parsed') and entry.published_parsed
                        else datetime.now(),
                    author=entry.get("author", "Brooklyn Eagle"),
                    categories=[tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []
                )
                
                # Filter for Kensington relevance
                if is_kensington_relevant(item):
                    items.append(item)
            except Exception as e:
                logger.warning(f"Error parsing entry: {e}")
        
        return items
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {e}")
        return []


def save_items(items, start_date=None, end_date=None):
    """Save scraped items to date-organized folders."""
    if not items:
        logger.info("No items to save")
        return 0
    
    # Determine date range for saving
    if start_date and end_date:
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        current = datetime.now()
        end_dt = current
    
    saved_count = 0
    
    while current <= end_dt:
        date_str = current.strftime("%Y-%m-%d")
        day_dir = SCRAPE_ITEMS_DIR / date_str
        day_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter items for this day
        start_date_obj = datetime.strptime(start_date or date_str, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date or date_str, "%Y-%m-%d").date()
        day_items = [
            item for item in items
            if item.published_at and 
               start_date_obj <= item.published_at.date() <= end_date_obj
        ]
        
        # Save each item as separate JSON file
        for item in day_items:
            filename = f"{SOURCE_NAME}_{date_str}_{item.id[:50]}.json"
            filepath = day_dir / filename
            
            if not filepath.exists():  # Only save new items
                with open(filepath, "w") as f:
                    json.dump(item.model_dump(), f, indent=2, default=str)
                saved_count += 1
        
        current += timedelta(days=1)
    
    logger.info(f"Saved {saved_count} items to {SCRAPE_ITEMS_DIR}")
    return saved_count


def get_last_full_day() -> tuple[str, str]:
    """Get date range for last full day (yesterday 12:01am → 11:59pm)."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Brooklyn Eagle RSS feed for Kensington-relevant content"
    )
    parser.add_argument(
        "--last-day",
        action="store_true",
        help="Only scrape last full day (12:01am EST → 11:59pm)"
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Scrape items since date (YYYY-MM-DD)"
    )
    args = parser.parse_args()
    
    logger.info(f"Starting {SOURCE_NAME} scraper")
    
    # Determine date range
    if args.last_day:
        start_date, end_date = get_last_full_day()
        logger.info(f"Scraping last full day: {start_date}")
    elif args.since:
        start_date = args.since
        end_date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Scraping from {start_date} to {end_date}")
    else:
        # Default: scrape today and yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        start_date, end_date = yesterday, today
        logger.info(f"Scraping from {start_date} to {end_date}")
    
    # Parse RSS feed
    items = parse_rss_feed()
    logger.info(f"Found {len(items)} Kensington-relevant items")
    
    # Save items
    saved = save_items(items, start_date=start_date, end_date=end_date)
    logger.info(f"Scraping complete. Saved {saved} new items.")


if __name__ == "__main__":
    main()
