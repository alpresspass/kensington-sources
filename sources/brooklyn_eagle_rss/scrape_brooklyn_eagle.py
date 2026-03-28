#!/usr/bin/env python3
"""
Scrape Brooklyn Eagle RSS feed for Kensington-relevant news.

Brooklyn Eagle covers central/southern Brooklyn including Kensington, Windsor Terrace,
Flatbush, Ditmas Park, and surrounding neighborhoods.
"""

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List
import sys
import feedparser

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.rss_item import RSSItem

RSS_URL = "https://brooklyneagle.com/feed/"

# Keywords that indicate Kensington relevance
KENSINGTON_KEYWORDS = [
    "kensington", "windsor terrace", "flatbush", "ditmas park", 
    "midwood", "bensonhurst", "bay ridge", "sunset park",
    "myrtle avenue", "manhattan ave", "new york ave", "bushwick ave",
    "18th avenue", "mcdonald avenue", "church avenue", "fort hamilton pkwy",
    "11218", "11215", "11230", "11213"
]

def fetch_posts_for_date(target_date: date) -> List[RSSItem]:
    """
    Fetch Brooklyn Eagle RSS posts for a specific date.
    
    The RSS feed contains recent posts. We filter by date in Python.
    """
    print(f"Fetching from {RSS_URL}...")
    
    try:
        response = feedparser.parse(RSS_URL)
    except Exception as e:
        print(f"Error fetching RSS: {e}", file=sys.stderr)
        return []
    
    entries = response.entries
    print(f"Total entries in feed: {len(entries)}")
    
    # Convert target_date to boundaries for comparison
    start_dt = datetime(target_date.year, target_date.month, target_date.day)
    end_dt = start_dt + timedelta(days=1)
    
    all_posts: List[RSSItem] = []
    
    for entry in entries:
        try:
            # Parse publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            # Filter by date
            if not pub_date or not (start_dt <= pub_date < end_dt):
                continue
            
            # Check Kensington relevance
            title_lower = (entry.get('title') or '').lower()
            summary_lower = (entry.get('summary') or '').lower()
            combined_text = title_lower + " " + summary_lower
            
            is_kensington_related = any(kw in combined_text for kw in KENSINGTON_KEYWORDS)
            
            post_item = RSSItem(
                title=entry.get('title', ''),
                link=entry.get('link', ''),
                pub_date=pub_date,
                summary=(entry.get('summary') or '').replace('\n', ' ').strip(),
                author=entry.get('author', ''),
                is_kensington_related=is_kensington_related,
            )
            all_posts.append(post_item)
            
        except (KeyError, ValueError) as e:
            continue  # Skip malformed entries
    
    print(f"Posts from target date ({target_date}): {len(all_posts)}")
    return all_posts


def save_posts(posts: List[RSSItem], target_date: date, output_dir: Path) -> None:
    """
    Save posts to a JSON file for the given date.
    """
    import json
    
    # Create date folder if needed
    date_folder = output_dir / target_date.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    output_file = date_folder / f"brooklyn_eagle_{target_date.strftime('%Y-%m-%d')}.json"
    
    posts_data = [
        {
            "title": p.title,
            "link": p.link,
            "pub_date": p.pub_date.isoformat() if p.pub_date else None,
            "summary": p.summary,
            "author": p.author,
            "is_kensington_related": p.is_kensington_related,
        }
        for p in posts
    ]
    
    with open(output_file, 'w') as f:
        json.dump(posts_data, f, indent=2)
    
    print(f"Saved {len(posts)} posts to {output_file}")


def log_scrape(target_date: date, count: int, success: bool = True) -> None:
    """
    Log the scrape operation.
    """
    log_file = Path(__file__).parent / "scrape_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {status} - Scraped {count} posts for {target_date}\n")


def main():
    parser = argparse.ArgumentParser(description="Scrape Brooklyn Eagle RSS feed")
    parser.add_argument("--date", type=str, help="Date to scrape (YYYY-MM-DD), default: today")
    parser.add_argument("--days-ago", type=int, default=0, help="Days ago from today")
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=args.days_ago)
    
    print(f"Scraping Brooklyn Eagle RSS for {target_date}")
    
    # Fetch posts
    posts = fetch_posts_for_date(target_date)
    
    if posts:
        # Save to file
        output_dir = Path(__file__).parent / "scrape_items"
        save_posts(posts, target_date, output_dir)
        
        # Show first few
        for post in posts[:5]:  # Show first 5
            kensington_flag = " [K]" if post.is_kensington_related else ""
            print(f"  - {post.title[:60]}...{kensington_flag}")
    
    # Log the operation
    log_scrape(target_date, len(posts), success=True)


if __name__ == "__main__":
    main()
