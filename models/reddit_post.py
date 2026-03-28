from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RedditPostItem(BaseModel):
    """
    Represents a single Reddit post from r/Kensington.
    """
    title: str = Field(..., description="Post title")
    url: str = Field(..., description="Permalink to the post on Reddit")
    author: str = Field(..., description="Username of the poster (or [deleted])")
    score: int = Field(..., description="Upvote score")
    num_comments: int = Field(default=0, description="Number of comments")
    created_utc: int = Field(..., description="Unix timestamp when post was created")
    selftext: Optional[str] = Field(default="", max_length=500, description="Post body text (first 500 chars)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Local business opening on Knickerbocker Ave",
                "url": "https://reddit.com/r/kensington/comments/abc123/",
                "author": "kensington_resident",
                "score": 42,
                "num_comments": 8,
                "created_utc": 1703260800,
                "selftext": "Hey neighbors, just wanted to share that..."
            }
        }
