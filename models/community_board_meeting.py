"""
Community Board Meeting Item model for Brooklyn Community Board 6.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CommunityBoardMeetingItem(BaseModel):
    """
    A meeting minute or agenda item from Brooklyn Community Board 6.
    
    Fields:
        title: The title of the meeting or agenda item
        date: Date of the meeting (for minutes) or scheduled meeting (for agendas)
        url: Link to the full meeting page or PDF
        content_type: 'minutes' or 'agenda'
        topics: List of topics discussed or planned for discussion
    """
    title: str = Field(..., description="Title of the meeting")
    date: datetime = Field(..., description="Date of the meeting")
    url: str = Field(..., description="URL to the meeting page or PDF")
    content_type: str = Field(..., description="Type: 'minutes' or 'agenda'")
    topics: List[str] = Field(default=[], description="Topics discussed or planned")
