"""
Base Pydantic models for Kensington Free Press ScrapeItems.

All ScrapeItem types inherit from BaseScrapeItem and include:
- Unique identifier
- Content that can produce headlines
- Timestamps
- Source metadata
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class SourceMetadata(BaseModel):
    """Metadata about the source of a ScrapeItem."""
    name: str = Field(..., description="Name of the source (e.g., 'greenpointers_rss')")
    url: str = Field(..., description="URL of the source")
    type: str = Field(
        ..., 
        description="Type of source: rss_feed, subreddit, government_site, community_org, etc."
    )


class BaseScrapeItem(BaseModel):
    """
    Base model for all ScrapeItems.
    
    A ScrapeItem represents a single piece of content that can be scraped
    from a source and potentially used to generate headlines for KFP.
    """
    id: str = Field(..., description="Unique identifier for this item")
    title: str = Field(..., description="Title/headline of the content")
    published_at: datetime = Field(
        ..., 
        description="When this content was published"
    )
    source_metadata: SourceMetadata = Field(
        ..., 
        description="Metadata about the source"
    )
    
    def can_produce_headline(self) -> bool:
        """
        Check if this ScrapeItem can produce a headline for KFP.
        
        Returns True if title exists and is non-empty.
        Subclasses may override with more specific logic.
        """
        return bool(self.title and len(self.title.strip()) > 0)
    
    def get_headline(self) -> Optional[str]:
        """
        Extract a headline from this ScrapeItem.
        
        Returns the title if it can produce a headline, None otherwise.
        Subclasses may override with more specific logic.
        """
        return self.title if self.can_produce_headline() else None
