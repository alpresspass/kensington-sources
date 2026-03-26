"""RSS feed scraper for news feeds."""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import feedparser
except ImportError:
    print("feedparser not installed. Install with: pip install feedparser")
    sys.exit(1)

# Handle both relative and absolute imports
try:
    from .base_scraper import BaseScraper, ScrapeItem
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from base_scraper import BaseScraper, ScrapeItem


class RSSFeedScraper(BaseScraper):
    """Scraper for RSS feeds."""
    
    @property
    def scraper_name(self) -> str:
        return "rss_feed_scraper"
    
    def scrape(self, start_date: str, end_date: str) -> list[ScrapeItem]:
        """Scrape RSS feed for the given date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (inclusive)
            end_date: End date in YYYY-MM-DD format (inclusive)
            
        Returns:
            List of ScrapeItem objects found
        """
        config = self._load_source_config()
        source_client_key = config.get("source_client_key", {})
        
        # Try multiple ways to get the URL
        url = source_client_key.get("url")
        if not url:
            how_to_access = source_client_key.get("how_to_access", "")
            if "URL:" in how_to_access:
                url = how_to_access.split("URL:")[-1].strip().split()[0]
        
        if not url:
            self._log(f"No URL found for {self.source_path.name}")
            return []
        
        all_items: list[ScrapeItem] = []
        today_str = date.today().isoformat()
        items_for_today: list[ScrapeItem] = []
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:50]:  # Limit to first 50 entries
                title = getattr(entry, 'title', 'Untitled') or 'Untitled'
                
                # Get content - prefer summary over description
                content = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
                if not content:
                    content_elem = getattr(entry, 'content', [])
                    if content_elem:
                        content = content_elem[0].get('value', '') if isinstance(content_elem[0], dict) else str(content_elem[0])
                
                url_entry = getattr(entry, 'link', url)
                
                # Parse published date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                    except (TypeError, ValueError):
                        pass
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    except (TypeError, ValueError):
                        pass
                
                item = ScrapeItem(
                    title=title,
                    content=content,
                    url=url_entry,
                    published_at=pub_date,
                    source=self.source_path.name,
                    scrape_type="rss"
                )
                items_for_today.append(item)
            
            all_items.extend(items_for_today)
            
            # Check if we have new items
            new_hashes = {self._item_hash(item) for item in items_for_today}
            if self._has_new_items(today_str, new_hashes):
                self._log(f"New RSS items found for {self.source_path.name}: {len(items_for_today)} items")
                filename = f"{self.source_path.stem}_{today_str}"
                self._save_items(today_str, filename, items_for_today)
            
        except Exception as e:
            self._log(f"Error parsing RSS feed {url}: {e}")
        
        return all_items
