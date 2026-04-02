#!/usr/bin/env python3
"""
Scrape posts from r/BedStuy subreddit.

Bed-Stuy is adjacent to Kensington and often has relevant local news,
safety updates, community events that affect the broader area.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import requests
from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    """A post from a Reddit subreddit."""
    id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title/headline")
    author: str = Field(..., description="Post author (can be [deleted])")
    created_utc: int = Field(..., description="Unix timestamp when post was created")
    url: str = Field(..., description="URL to the Reddit post")
    permalink: str = Field(..., description="Reddit's permanent link format")
    score: int = Field(default=0, description="Upvote score")
    num_comments: int = Field(default=0, description="Number of comments")
    selftext: str = Field(default="", description="Post body text (if any)")
    is_self: bool = Field(default=False, description="True if post contains text content")
    link_flair_text: Optional[str] = Field(default=None, description="Flair text if present")


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
    
    headers = {
        "User-Agent": "KensingtonFreePress/1.0 (by /u/KFP-Bot)"
    }
    
    all_posts: list[dict] = []
    after_token = None
    
    while True:
        url = base_url
        if after_token:
            url += f"&after={after_token}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = data["data"]["children"]
            all_posts.extend(posts)
            
            # Check for pagination
            after_token = data["data"]["after"]
            if not after_token or len(posts) == 0:
                break
                
        except requests.RequestException as e:
            print(f"Error fetching from {url}: {e}")
            break
    
    # Filter by time range if specified
    filtered_posts = []
    for post_data in all_posts:
        post_info = post_data["data"]
        post_time = datetime.fromtimestamp(post_info["created_utc"], tz=timezone.utc)
        
        if since and post_time < since:
            continue
        if until and post_time > until:
            continue
            
        filtered_posts.append(post_data)
    
    # Convert to Pydantic models
    posts = []
    for post_data in filtered_posts:
        post_info = post_data["data"]
        try:
            post = RedditPost(
                id=post_info["id"],
                title=post_info["title"],
                author=post_info.get("author", "[deleted]"),
                created_utc=post_info["created_utc"],
                url=f"https://reddit.com{post_info['permalink']}",
                permalink=post_info["permalink"],
                score=post_info.get("score", 0),
                num_comments=post_info.get("num_comments", 0),
                selftext=post_info.get("selftext", ""),
                is_self=post_info.get("is_self", False),
                link_flair_text=post_info.get("link_flair_text")
            )
            posts.append(post)
        except Exception as e:
            print(f"Error parsing post: {e}")
    
    return posts


def main():
    """Main scraping function."""
    subreddit = "BedStuy"
    
    # Get current time in EST (UTC-5)
    est_tz = timezone.utc  # Simplified - using UTC for consistency
    now = datetime.now(est_tz)
    today_str = now.strftime("%Y-%m-%d")
    
    # Parse arguments for time range (optional)
    since = None
    until = None
    
    import sys
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--since" and i + 1 < len(args):
            since_str = args[i + 1]
            since = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
            i += 2
        elif args[i] == "--until" and i + 1 < len(args):
            until_str = args[i + 1]
            until = datetime.fromisoformat(until_str.replace("Z", "+00:00"))
            i += 2
        else:
            i += 1
    
    # Default to today's posts only (last 26 hours with buffer)
    if since is None:
        since = now - timedelta(hours=26)  # Extra hour buffer
    
    print(f"Fetching posts from r/{subreddit}...")
    posts = get_reddit_posts(subreddit, since=since, until=until)
    
    if not posts:
        print("No new posts found.")
        return
    
    print(f"Found {len(posts)} posts")
    
    # Create output directory for today's date
    base_dir = Path(__file__).parent
    scrape_items_dir = base_dir / "scrape_items" / today_str
    scrape_items_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON file
    output_file = scrape_items_dir / f"r_bedstuy_{today_str}.json"
    posts_data = [post.model_dump() for post in posts]
    
    with open(output_file, "w") as f:
        json.dump(posts_data, f, indent=2)
    
    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()
