#!/usr/bin/env python3
"""
Scrape Reddit posts from Brooklyn neighborhood subreddits relevant to Kensington.

Note: r/kensington is for London, not Brooklyn! We use:
- r/Brooklyn (main Brooklyn subreddit)
- r/Greenpoint (nearby neighborhood)  
- r/Bushwick (adjacent to Kensington)
"""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List
import sys
import urllib.request
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.subreddit_post import SubredditPostItem

# Brooklyn neighborhood subreddits relevant to Kensington area (11218)
BROOKLYN_SUBREDDITS = [
    "Brooklyn",      # Main Brooklyn subreddit - most active
    "Greenpoint",    # Nearby neighborhood, often covers Kensington
    "Bushwick",      # Adjacent to Kensington
]

def fetch_posts_for_date(target_date: date) -> List[SubredditPostItem]:
    """
    Fetch Reddit posts from Brooklyn subreddits for a specific date.
    
    Uses Reddit's public JSON API (no authentication needed for hot/new posts).
    Filters by date in Python since Reddit doesn't support date filtering.
    """
    # Convert target_date to Unix timestamp boundaries
    start_dt = datetime(target_date.year, target_date.month, target_date.day)
    end_dt = start_dt + timedelta(days=1)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    
    all_posts: List[SubredditPostItem] = []
    total_fetched = 0
    
    for subreddit in BROOKLYN_SUBREDDITS:
        try:
            print(f"Fetching from r/{subreddit}...")
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            posts_data = data.get("data", {}).get("children", [])
            total_fetched += len(posts_data)
            
            for post_data in posts_data:
                try:
                    # Filter by date (created_utc is Unix timestamp)
                    created_ts = int(post_data["data"]["created_utc"])
                    if not (start_ts <= created_ts < end_ts):
                        continue
                    
                    # Check if post mentions Kensington area keywords
                    title_lower = post_data["data"].get("title", "").lower()
                    selftext_lower = post_data["data"].get("selftext", "").lower() or ""
                    combined_text = title_lower + " " + selftext_lower
                    
                    # Keywords that might indicate Kensington relevance
                    kensington_keywords = [
                        "kensington", "myrtle avenue", "manhattan ave", 
                        "new york ave", "bushwick ave", "11218"
                    ]
                    is_kensington_related = any(kw in combined_text for kw in kensington_keywords)
                    
                    post_item = SubredditPostItem(
                        title=post_data["data"].get("title", ""),
                        author=post_data["data"].get("author", ""),
                        subreddit=f"r/{subreddit}",
                        url=f"https://www.reddit.com{post_data['data'].get('permalink', '')}",
                        created_at=datetime.fromtimestamp(created_ts),
                        score=post_data["data"].get("score", 0),
                        num_comments=post_data["data"].get("num_comments", 0),
                        selftext=post_data["data"].get("selftext", "") or "",
                        is_kensington_related=is_kensington_related,
                    )
                    all_posts.append(post_item)
                    
                except (KeyError, ValueError) as e:
                    continue  # Skip malformed posts
            
            # Rate limit protection
            time.sleep(1.5)
            
        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}", file=sys.stderr)
            continue
    
    print(f"Total posts fetched: {total_fetched}")
    print(f"Posts from target date ({target_date}): {len(all_posts)}")
    return all_posts


def save_posts(posts: List[SubredditPostItem], target_date: date, output_dir: Path) -> None:
    """
    Save posts to a JSON file for the given date.
    """
    # Create date folder if needed
    date_folder = output_dir / target_date.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    output_file = date_folder / f"reddit_posts_{target_date.strftime('%Y-%m-%d')}.json"
    
    posts_data = [
        {
            "title": p.title,
            "author": p.author,
            "subreddit": p.subreddit,
            "url": p.url,
            "created_at": p.created_at.isoformat(),
            "score": p.score,
            "num_comments": p.num_comments,
            "selftext": p.selftext,
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
    parser = argparse.ArgumentParser(description="Scrape Reddit posts from Brooklyn subreddits")
    parser.add_argument("--date", type=str, help="Date to scrape (YYYY-MM-DD), default: today")
    parser.add_argument("--days-ago", type=int, default=0, help="Days ago from today")
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=args.days_ago)
    
    print(f"Scraping Reddit posts for {target_date}")
    print(f"Subreddits: {', '.join(BROOKLYN_SUBREDDITS)}")
    
    # Fetch posts
    posts = fetch_posts_for_date(target_date)
    
    print(f"Found {len(posts)} posts from target date")
    
    if posts:
        # Save to file
        output_dir = Path(__file__).parent / "scrape_items"
        save_posts(posts, target_date, output_dir)
        
        # Show first few
        for post in posts[:5]:  # Show first 5
            print(f"  - [{post.subreddit}] {post.title[:60]}... (score: {post.score})")
    
    # Log the operation
    log_scrape(target_date, len(posts), success=len(posts) >= 0)


if __name__ == "__main__":
    main()
