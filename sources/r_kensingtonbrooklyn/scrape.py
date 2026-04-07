#!/usr/bin/env python3
"""
Scrape posts from r/KensingtonBrooklyn subreddit.

Usage:
    uv run scrape.py [--since YYYY-MM-DD] [--until YYYY-MM-DD]
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Optional
import requests
from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    """A post from r/KensingtonBrooklyn subreddit."""
    id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title/headline")
    author: str = Field(..., description="Post author (username)")
    created_utc: int = Field(..., description="Unix timestamp when post was created")
    url: str = Field(..., description="URL to the Reddit post")
    permalink: str = Field(..., description="Reddit permalink")
    num_comments: int = Field(default=0, description="Number of comments on the post")
    score: int = Field(default=0, description="Upvote score")
    selftext: str = Field(default="", description="Post body text (if any)")
    is_self: bool = Field(default=False, description="Whether this is a self-post (text post)")
    thumbnail: str = Field(default="", description="Thumbnail URL if available")


def get_reddit_posts(
    subreddit: str,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None
) -> list[RedditPost]:
    """
    Fetch posts from a Reddit subreddit.
    
    Uses Reddit's JSON API endpoint which doesn't require authentication for reading.
    Uses 'new' sorting to get recent posts, then filters by time range.
    """
    base_url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=100"
    
    all_posts = []
    after = None
    
    while True:
        url = base_url if not after else f"https://www.reddit.com/r/{subreddit}/hot.json?limit=100&after={after}"
        
        try:
            response = requests.get(url, headers={
                "User-Agent": "KensingtonFreePress/1.0 (by /u/alpresspass)"
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            
        except requests.RequestException as e:
            print(f"Error fetching from Reddit: {e}")
            break
        
        posts_data = data.get("data", {}).get("children", [])
        if not posts_data:
            break
            
        for post_data in posts_data:
            post_info = post_data.get("data", {})
            try:
                post = RedditPost(
                    id=post_info.get("id", ""),
                    title=post_info.get("title", ""),
                    author=post_info.get("author", ""),
                    created_utc=post_info.get("created_utc", 0),
                    url=post_info.get("url", ""),
                    permalink=f"https://www.reddit.com{post_info.get('permalink', '')}",
                    num_comments=post_info.get("num_comments", 0),
                    score=post_info.get("score", 0),
                    selftext=post_info.get("selftext", ""),
                    is_self=post_info.get("is_self", False),
                    thumbnail=post_info.get("thumbnail", "")
                )
                all_posts.append(post)
            except Exception as e:
                print(f"Error parsing post: {e}")
                continue
        
        # Check for pagination
        after = data.get("data", {}).get("after")
        if not after:
            break
            
        # Safety limit
        if len(all_posts) >= 200:
            break
    
    return all_posts


def main():
    parser = argparse.ArgumentParser(description="Scrape r/KensingtonBrooklyn posts")
    parser.add_argument("--since", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", type=str, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    # Parse dates
    since_dt: Optional[datetime] = None
    until_dt: Optional[datetime] = None
    
    if args.since:
        since_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if args.until:
        # End of day for "until" date
        until_dt = datetime.strptime(args.until, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    
    # Get today's date for storage folder
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Determine output filename
    if args.since and args.until:
        output_filename = f"r_kensingtonbrooklyn_{args.since}_to_{args.until}.json"
    elif args.since:
        output_filename = f"r_kensingtonbrooklyn_since_{args.since}.json"
    else:
        output_filename = f"r_kensingtonbrooklyn_{today}.json"
    
    # Get repo root (parent of sources/)
    repo_root = Path(__file__).parent.parent.parent
    
# Create scrape_items directory
    scrape_items_dir = repo_root / f"scrape_items/{today}"
    scrape_items_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch posts
    print(f"Fetching posts from r/KensingtonBrooklyn...")
    posts = get_reddit_posts("KensingtonBrooklyn", since_dt, until_dt)
    
    if not posts:
        print("No posts found.")
        return
    
    # Filter by date range if specified
    filtered_posts = []
    for post in posts:
        post_dt = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
        if since_dt and post_dt < since_dt:
            continue
        if until_dt and post_dt > until_dt:
            continue
        filtered_posts.append(post)
    
    print(f"Found {len(filtered_posts)} posts")
    
    # Save to file
    output_path = scrape_items_dir / output_filename
    with open(output_path, "w") as f:
        json.dump([post.model_dump() for post in filtered_posts], f, indent=2)
    print(f"Saved to {output_path}")
    
    # Update scrape_log.txt (in source folder)
    log_entry = f"{datetime.now(timezone.utc).isoformat()} - Scraped r/KensingtonBrooklyn: {len(filtered_posts)} posts -> {output_filename}\n"
    with open(repo_root / "sources/r_kensingtonbrooklyn/scrape_log.txt", "a") as f:
        f.write(log_entry)


if __name__ == "__main__":
    main()
