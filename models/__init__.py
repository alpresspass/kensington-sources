"""
Pydantic models for Kensington Free Press scrapers.

Each source type has its own ScrapeItem model.
"""

from .base import BaseScrapeItem
from .rss_item import RSSItem
from .event_item import EventItem
from .alert_item import AlertItem
from .reddit_post import RedditPostItem
from .community_board_meeting import CommunityBoardMeetingItem
from .building_permit import BuildingPermitItem

__all__ = [
    "BaseScrapeItem",
    "RSSItem",
    "EventItem",
    "AlertItem",
    "RedditPostItem",
    "CommunityBoardMeetingItem",
    "BuildingPermitItem",
]
