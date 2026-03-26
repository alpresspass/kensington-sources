"""
Event ScrapeItem model.

Used for scraping events from:
- Eventbrite (local events)
- Meetup groups
- Community calendars
- Restaurant event pages
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import re


class EventItem(BaseModel):
    """
    ScrapeItem for events.
    
    Events in Kensington area that could be news-worthy:
    - Community meetings
    - Restaurant openings/events
    - Cultural events
    - Political rallies/meetings
    """
    id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event name/title")
    description: Optional[str] = Field(None, description="Event description")
    url: str = Field(..., description="URL to event page")
    
    # Event timing
    start_time: datetime = Field(..., description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    is_all_day: bool = Field(default=False, description="Whether this is an all-day event")
    
    # Location
    venue_name: Optional[str] = Field(None, description="Venue name")
    address: Optional[str] = Field(None, description="Event address")
    neighborhood: Optional[str] = Field(None, description="Neighborhood if known")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    
    # Event details
    is_free: bool = Field(default=True, description="Whether event is free (default true)")
    price_range: Optional[str] = Field(None, description="Price range if not free")
    capacity: Optional[int] = Field(None, description="Event capacity")
    available_tickets: Optional[int] = Field(None, description="Tickets remaining")
    
    # Organizer info
    organizer_name: Optional[str] = Field(None, description="Organizer name")
    organizer_url: Optional[str] = Field(None, description="Organizer profile URL")
    
    # Categories/tags
    categories: Optional[List[str]] = Field(None, description="Event categories")
    
    def is_kensington_area(self) -> bool:
        """
        Check if event is in Kensington area.
        
        Checks venue name, address, and neighborhood for Kensington-area terms.
        """
        kensington_terms = [
            'kensington', 'greenpoint', 'williamsburg', 'bushwick',
            'bedford-stuyvesant', 'bed-stuy', 'east williamsburg',
            '11218', '11222', '11249'
        ]
        
        text_to_check = ""
        if self.venue_name:
            text_to_check += " " + self.venue_name.lower()
        if self.address:
            text_to_check += " " + self.address.lower()
        if self.neighborhood:
            text_to_check += " " + self.neighborhood.lower()
            
        return any(term in text_to_check for term in kensington_terms)
    
    def get_headline_candidate(self) -> str:
        """
        Generate a headline candidate from event info.
        
        Format: "[Event Name] at [Venue] on [Date]"
        """
        parts = [self.title]
        if self.venue_name:
            parts.append(f"at {self.venue_name}")
        if self.start_time:
            date_str = self.start_time.strftime("%B %d")
            parts.append(date_str)
            
        return " ".join(parts)[:150]
