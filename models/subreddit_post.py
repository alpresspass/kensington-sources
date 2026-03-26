"""
Subreddit Post ScrapeItem model.

Used for scraping posts from local subreddits:
- r/KensingtonBrooklyn
- r/Greenpoint
- r/Williamsburg
- r/Bushwick
- r/Brooklyn
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import re


class SubredditPostItem(BaseModel):
    """
    ScrapeItem for Reddit posts.
    
    Captures posts from local subreddits that may contain:
    - Local news tips
    - Community discussions
    - Event announcements
    - Restaurant/business updates
    """
    id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title")
    selftext: Optional[str] = Field(None, description="Post body text (if any)")
    url: str = Field(..., description="URL to the Reddit post")
    
    # Post metadata
    subreddit: str = Field(..., description="Subreddit name (without r/)")
    author: Optional[str] = Field(None, description="Post author (may be deleted)")
    created_utc: datetime = Field(..., description="Post creation time")
    
    # Engagement metrics
    score: int = Field(default=0, description="Upvote score")
    num_comments: int = Field(default=0, description="Number of comments")
    upvote_ratio: Optional[float] = Field(None, description="Upvote ratio (0-1)")
    
    # Post type
    is_self: bool = Field(default=False, description="Whether post has selftext")
    is_video: bool = Field(default=False, description="Whether post contains video")
    domain: Optional[str] = Field(None, description="Domain of linked content (if external)")
    
    # Media
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    media_url: Optional[str] = Field(None, description="Direct media URL if available")
    
    # Flair
    link_flair_text: Optional[str] = Field(None, description="Post flair text")
    link_flair_background_color: Optional[str] = Field(None, description="Flair background color hex")
    
    def is_news_worthy(self) -> bool:
        """
        Determine if post might be news-worthy.
        
        Checks for:
        - High engagement (score > 10 or comments > 5)
        - News-related flair
        - Links to external sources
        """
        # Check engagement
        if self.score >= 10 or self.num_comments >= 5:
            return True
            
        # Check for news flairs
        news_flairs = ['news', 'update', 'announcement', 'important']
        if self.link_flair_text:
            flair_lower = self.link_flair_text.lower()
            if any(flair in flair_lower for flair in news_flairs):
                return True
                
        # Check if linking to external source (might be sharing news)
        if self.domain and not self.is_self:
            news_domains = ['nytimes', 'wsj', 'cnn', 'abc', 'nbc', 'fox', 'amny']
            if any(domain in self.domain.lower() for domain in news_domains):
                return True
                
        return False
    
    def get_headline_candidate(self) -> str:
        """
        Generate headline from post title.
        
        Adds subreddit context if helpful.
        """
        # Clean up title
        cleaned = re.sub(r'\s+', ' ', self.title.strip())
        
        # Limit length
        if len(cleaned) > 120:
            cleaned = cleaned[:117] + "..."
            
        return cleaned
    
    def get_source_attribution(self) -> str:
        """
        Get source attribution string.
        
        Format: "via r/[subreddit]"
        """
        return f"via r/{self.subreddit}"
