"""
Alert ScrapeItem model.

Used for scraping service alerts from:
- MTA (subway/bus service changes)
- NYC311 (road closures, construction)
- Other alert-based sources
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

# Import base models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from .base import BaseScrapeItem


class AlertItem(BaseScrapeItem):
    """
    ScrapeItem for service alerts.
    
    Represents a single alert (e.g., MTA service change) that can be used
    to generate headlines like "G Trains not running past Church Ave this week."
    """
    description: str = Field(
        ..., 
        description="Detailed description of the alert"
    )
    url: str = Field(
        ..., 
        description="URL to view more details about the alert"
    )
    affected_lines: List[str] = Field(
        default=[],
        description="List of train/bus lines affected (e.g., ['G', 'L'])"
    )
    alert_type: str = Field(
        ..., 
        description="Type of alert: delay, closure, service_change, elevator_outage, etc."
    )
    source: str = Field(
        ..., 
        description="Source name (e.g., 'MTA', 'NYC311')"
    )
    
    def can_produce_headline(self) -> bool:
        """
        Check if this alert can produce a headline for KFP.
        
        Returns True if title exists and describes an actionable alert.
        """
        has_title = bool(self.title and len(self.title.strip()) > 0)
        is_actionable = self.alert_type in ['delay', 'closure', 'service_change']
        return has_title and is_actionable
    
    def get_headline(self) -> Optional[str]:
        """
        Extract a headline from this alert.
        
        Formats alerts as actionable headlines like:
        - "G Train service suspended between Church Ave and Forest Hills"
        - "L Train experiencing 10-minute delays"
        """
        if not self.can_produce_headline():
            return None
        
        # Clean up title
        headline = self.title.strip()
        
        # Add context from alert type if needed
        if self.alert_type == 'closure':
            if 'closed' not in headline.lower():
                headline = f"CLOSED: {headline}"
        elif self.alert_type == 'delay':
            if 'delay' not in headline.lower():
                headline = f"DELAYED: {headline}"
        
        return headline
