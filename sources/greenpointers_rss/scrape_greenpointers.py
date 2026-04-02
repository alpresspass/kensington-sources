#!/usr/bin/env python3
"""
Scrape GreenPointers RSS feed for Brooklyn news.

GreenPointers covers Greenpoint, Williamsburg, and surrounding areas -
news often relevant to Kensington residents.
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import requests
from feedparser import parse
from pydantic import BaseModel, Field


class RSSItem(BaseModel):
    """An item from an RSS feed."""
    title: str = Field(..., description="Article title/headline")
    link: str = Field(..., description="URL to the article")
    published: Optional[str] = Field(default=None, description="Published date string")
    author: Optional[str] = Field(default=None, description="Author name if available")
    summary: Optional[str] = Field(default=None, description="Article summary/description")


def fetch_greenpointers_feed() -> tuple[Optional[str], list[dict]]:
    """
    Fetch the GreenPointers RSS feed.
    
    Returns:
        Tuple of (feed_title, entries_list)
    """
    url = "https://greenpointers.com/feed/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed_data = parse(response.content)
        return feed_data.feed.get("title"), feed_data.entries
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return None, []


def filter_entries_by_date(
    entries: list[dict],
    start_date: datetime,
    end_date: datetime
) -> list[RSSItem]:
    """
    Filter RSS entries to only include those within the specified date range.
    
    Args:
        entries: List of raw entry dictionaries from feedparser
        start_date: Start of date range (inclusive)
        end_date: End of date range (exclusive)
    
    Returns:
        List of RSSItem objects filtered by date
    """
    filtered = []
    
    for entry in entries:
        # Try to get published date from parsed values
        pub_datetime = None
        
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_datetime = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            pub_datetime = datetime(*entry.updated_parsed[:6])
        
        # Skip entries without a valid date
        if pub_datetime is None:
            continue
        
        # Make pub_datetime timezone-aware (assume UTC for RSS feeds)
        if pub_datetime.tzinfo is None:
            pub_datetime = pub_datetime.replace(tzinfo=timezone.utc)
        
        # Check if within range
        if start_date <= pub_datetime < end_date:
            try:
                item = RSSItem(
                    title=entry.get("title", "Untitled"),
                    link=entry.get("link", "#"),
                    published=entry.get("published"),
                    author=entry.get("author"),
                    summary=entry.get("summary")
                )
                filtered.append(item)
            except Exception as e:
                print(f"Error parsing entry: {e}")
    
    return filtered


def main():
    """Main function to scrape GreenPointers RSS feed."""
    parser = argparse.ArgumentParser(description='Scrape GreenPointers RSS feed')
    parser.add_argument('--days-ago', type=int, default=1,
                       help='Number of days ago to fetch (default: 1 for yesterday)')
    args = parser.parse_args()
    
    # Calculate the target date range
    now = datetime.now(tz=timezone.utc)
    target_date = now - timedelta(days=args.days_ago)
    start_of_day = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)
    
    print(f"Fetching GreenPointers feed for {target_date.date()}...")
    print(f"  Start: {start_of_day}")
    print(f"  End:   {end_of_day}")
    
    # Fetch the feed
    feed_title, entries = fetch_greenpointers_feed()
    
    if not entries:
        print("No entries found in feed.")
        return
    
    print(f"Total entries in feed: {len(entries)}")
    
    # Filter by date range
    filtered_entries = filter_entries_by_date(entries, start_of_day, end_of_day)
    
    if not filtered_entries:
        print("No entries found for the specified date.")
        return
    
    print(f"Entries for {target_date.date()}: {len(filtered_entries)}")
    
    # Create output directory
    base_dir = Path(__file__).parent
    scrape_items_dir = base_dir / "scrape_items" / target_date.strftime("%Y-%m-%d")
    scrape_items_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON file
    output_file = scrape_items_dir / f"greenpointers_rss_{target_date.strftime('%Y-%m-%d')}.json"
    items_data = [item.model_dump() for item in filtered_entries]
    
    with open(output_file, "w") as f:
        json.dump(items_data, f, indent=2)
    
    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()
