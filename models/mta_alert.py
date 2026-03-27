"""
MTA Alert ScrapeItem models.

Used for scraping service status and alerts from MTA sources.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field

from .base import BaseScrapeItem


class MTAAlert(BaseScrapeItem):
    """
    A single MTA service alert.
    
    Contains information about subway/bus service changes,
    delays, and other transit-related news.
    """
    route: str = Field(..., description="Affected route(s) - e.g., 'G', 'Q', 'B47'")
    mode: str = Field(..., description="Transportation mode: subway, bus, lirr, or path")
    alert_type: str = Field(..., description="Type of alert: delay, service_change, construction, etc.")
    description: str = Field(..., description="Full alert description")
    severity: Optional[str] = Field(None, description="Alert severity if available")
    start_time: Optional[datetime] = Field(None, description="When the alert started or will start")
    end_time: Optional[datetime] = Field(None, description="Expected end time of the alert")