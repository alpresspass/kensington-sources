"""
RSS Article ScrapeItem model.

Used for scraping news articles from RSS feeds like:
- Greenpointers
- Brooklyn Eagle  
- 6sqft
- NY YIMBY
- And other local news RSS feeds
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

# Import base models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from .base import BaseScrapeItem, SourceMetadata


class RSSArticleItem(BaseScrapeItem):
    """
    ScrapeItem for RSS feed articles.
    
    Represents a single article from an RSS feed that can be used
    to generate headlines for Kensington Free Press.
    """
    link: str = Field(..., description="URL to the full article")
    summary: Optional[str] = Field(
        None, 
        description="Brief summary/excerpt of the article"
    )
    content: Optional[str] = Field(
        None,
        description="Full content of the article (if available)"
    )
    author: Optional[str] = Field(
        None,
        description="Author of the article"
    )
    categories: List[str] = Field(
        default=[],
        description="Categories/tags associated with the article"
    )
    
    def can_produce_headline(self) -> bool:
        """
        Check if this RSS article can produce a headline for KFP.
        
        Returns True if title exists and is non-empty, and summary
        or content provides context.
        """
        has_title = bool(self.title and len(self.title.strip()) > 0)
        has_content = bool(self.summary or self.content)
        return has_title and has_content
    
    def get_headline(self) -> Optional[str]:
        """
        Extract a headline from this RSS article.
        
        Returns the title if it can produce a headline, None otherwise.
        May add source attribution for clarity.
        """
        if not self.can_produce_headline():
            return None
        
        # Clean up title - remove excessive punctuation
        headline = self.title.strip()
        
        # Remove trailing colons or dashes that might indicate continuation
        headline = headline.rstrip(': -')
        
        return headline
