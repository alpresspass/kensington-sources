#!/usr/bin/env python3
"""
Scrape r/Kensington subreddit for local news and discussions.

Reddit API: https://www.reddit.com/dev/api/
No authentication needed for reading public posts.
"""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional
import sys
import urllib.request
import urllib.parse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.subreddit_post import SubredditPostItem


SUBREDDIT = "kensington"
API_URL = f"https://www.reddit.com/r/{SUBREDDIT}/hot.json?limit=100"


def fetch_posts_for_date(target_date: date) -> List[SubredditPostItem]:
    """
    Fetch posts from r/Kensington.
    
    Reddit's API doesn't have a great way to filter by exact date,
    so we fetch hot/new posts and filter client-side.
    """
    try:
        print(f"Fetching posts from r/{SUBREDDIT}...")
        
        with urllib.request.urlopen(API_URL, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Extract posts from the JSON structure
        posts_data = data.get("data", {}).get("children", [])
        
        posts = []
        target_date_str = target_date.strftime("%Y-%m-%d")
        today_midnight = datetime.combine(target_date, datetime.min.time())
        yesterday_midnight = today_midnight - timedelta(days=1)
        
        for child in posts_data:
            post_data = child.get("data", {})
            created_utc = post_data.get("created_utc", 0)
            post_datetime = datetime.fromtimestamp(created_utc, tz=None)
            
            # Filter by date (last 48 hours to catch recent posts)
            if not (yesterday_midnight - timedelta(hours=24) <= post_datetime < today_midnight + timedelta(days=1)):
                continue
            
            try:
                post = SubredditPostItem(
                    id=post_data.get("id", ""),
                    title=post_data.get("title", ""),
                    author=post_data.get("author", ""),
                    subreddit=SUBREDDIT,
                    url=post_data.get("url", ""),
                    permalink=f"/r/{SUBREDDIT}/comments/{post_data.get('id', '')}/{post_data.get('title', '').lower().replace(' ', '_')}/",
                    score=post_data.get("score", 0),
                    num_comments=post_data.get("num_comments", 0),
                    created_utc=created_utc,
                    selftext=post_data.get("selftext", "")[:500] if post_data.get("selftext") else None,  # Truncate
                )
                posts.append(post)
            except Exception as e:
                continue
        
        return posts
        
    except Exception as e:
        print(f"Error fetching posts: {e}", file=sys.stderr)
        return []


def save_posts(posts: List[SubredditPostItem], target_date: date, output_dir: Path) -> None:
    """
    Save posts to a JSON file for the given date.
    """
    # Create date folder if needed
    date_folder = output_dir / target_date.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    output_file = date_folder / f"r_kensington_{target_date.strftime('%Y-%m-%d')}.json"
    
    posts_data = [
        {
            "id": p.id,
            "title": p.title,
            "author": p.author,
            "subreddit": p.subreddit,
            "url": p.url,
            "permalink": p.permalink,
            "score": p.score,
            "num_comments": p.num_comments,
            "created_utc": p.created_utc,
            "selftext": p.selftext,
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
    parser = argparse.ArgumentParser(description="Scrape r/Kensington subreddit")
    parser.add_argument("--date", type=str, help="Date to scrape (YYYY-MM-DD), default: today")
    parser.add_argument("--days-ago", type=int, default=0, help="Days ago from today")
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=args.days_ago)
    
    print(f"Scraping r/Kensington for {target_date}")
    
    # Fetch posts
    posts = fetch_posts_for_date(target_date)
    
    print(f"Found {len(posts)} posts")
    
    if posts:
        # Save to file
        output_dir = Path(__file__).parent / "scrape_items"
        save_posts(posts, target_date, output_dir)
        
        # Show first few
        for post in posts[:5]:
            print(f"  - [{post.score} pts] {post.title}")
    
    # Log the operation
    log_scrape(target_date, len(posts), success=True)


if __name__ == "__main__":
    main()
