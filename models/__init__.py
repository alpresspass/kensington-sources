"""
Pydantic models for Kensington Free Press scrapers.

Each source type has its own ScrapeItem model.
"""

from .base import BaseScrapeItem
from .rss_item import RSSArticleItem
from .event_item import EventItem
from .alert_item import AlertItem
from .subreddit_post import SubredditPostItem

__all__ = [
    "BaseScrapeItem",
    "RSSArticleItem",
    "EventItem",
    "AlertItem",
    "SubredditPostItem",
]
