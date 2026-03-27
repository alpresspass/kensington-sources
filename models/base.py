"""
Base Pydantic models for Kensington Free Press ScrapeItems.

All ScrapeItem types inherit from BaseScrapeItem and include:
- Unique identifier
- Content that can produce headlines
- Timestamps
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


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