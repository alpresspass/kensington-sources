#!/usr/bin/env python3
"""
Scrape r/Kensington subreddit for posts.

Uses PRAW (Python Reddit API Wrapper) to access Reddit's official API.
Filters posts by date range using created_utc timestamp.
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import sys

try:
    import praw
except ImportError:
    print("Error: praw not installed. Run: uv add praw")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.reddit_post import RedditPostItem


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape r/Kensington posts")
    parser.add_argument("--days-ago", type=int, default=1,
                       help="Number of days back to fetch (default: 1)")
    parser.add_argument("--start-date", type=str, 
                       help="Start date in YYYY-MM-DD format (optional)")
    parser.add_argument("--end-date", type=str, 
                       help="End date in YYYY-MM-DD format (optional)")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Calculate date range
    if args.start_date and args.end_date:
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d") + timedelta(days=1)
    else:
        now = datetime.now()
        end_dt = now
        start_dt = now - timedelta(days=args.days_ago)
    
    # Convert to Unix timestamps (Reddit uses UTC)
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(end_dt.timestamp())
    
    print(f"Fetching r/Kensington posts from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
    print(f"Timestamp range: {start_timestamp} - {end_timestamp}")
    
    # Initialize Reddit API
    try:
        reddit = praw.Reddit(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET", 
            user_agent="kensington-sources/1.0 (by /u/kensington-free-press)",
            check_for_async=False
        )
    except Exception as e:
        print(f"Error initializing Reddit API: {e}")
        print("\nNote: You need to set up Reddit API credentials.")
        print("1. Go to https://www.reddit.com/prefs/apps")
        print("2. Create an app (type: 'script')")
        print("3. Update client_id and client_secret in this script")
        sys.exit(1)
    
    subreddit = reddit.subreddit("kensington")
    posts_collected: List[RedditPostItem] = []
    
    # Fetch posts - we need to fetch more than needed since we're filtering by date
    # Reddit's "new" sorting gets the most recent posts first
    print("Fetching posts from subreddit...")
    
    try:
        for post in subreddit.new(limit=100):  # Fetch last 100 new posts
            created_utc = int(post.created_utc)
            
            # Check if post is within our date range
            if start_timestamp <= created_utc < end_timestamp:
                post_item = RedditPostItem(
                    title=post.title,
                    url=f"https://reddit.com{post.permalink}",
                    author=post.author.name if post.author else "[deleted]",
                    score=post.score,
                    num_comments=post.num_comments,
                    created_utc=created_utc,
                    selftext=post.selftext[:500] if hasattr(post, 'selftext') else ""  # First 500 chars of body
                )
                posts_collected.append(post_item)
                print(f"  ✓ Found: {post.title[:60]}... (score: {post.score})")
            
            # If we've gone past our start date, stop fetching
            if created_utc < start_timestamp:
                break
                
    except Exception as e:
        print(f"Error fetching posts: {e}")
        sys.exit(1)
    
    # Sort by newest first
    posts_collected.sort(key=lambda x: x.created_utc, reverse=True)
    
    # Save to file
    date_str = start_dt.strftime("%Y-%m-%d")
    output_dir = Path(__file__).parent / "posts" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "posts.json"
    data = {
        "date": date_str,
        "count": len(posts_collected),
        "posts": [post.model_dump() for post in posts_collected]
    }
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\nSaved {len(posts_collected)} posts to {output_file}")
    
    # Update scrape log
    log_file = Path(__file__).parent / "scrape_log.txt"
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scraped r/Kensington: {len(posts_collected)} posts for {date_str}\n")


if __name__ == "__main__":
    main()
