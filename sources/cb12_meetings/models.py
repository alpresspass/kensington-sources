from pydantic import BaseModel, HttpUrl
from datetime import date

class CB12Meeting(BaseModel):
    """Brooklyn Community Board 12 meeting information."""
    meeting_date: str  # e.g., "Tuesday, January 27 at 7:00 PM"
    month_name: str  # e.g., "January"
    agenda_url: HttpUrl | None = None
    zoom_url: HttpUrl | None = None
    scraped_on: date