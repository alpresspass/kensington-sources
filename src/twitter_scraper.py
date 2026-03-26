"""Twitter/X scraper."""

import hashlib
import sys
from datetime import date
from pathlib import Path
from typing import Any

import requests

# Handle both relative and absolute imports
try:
    from .base_scraper import BaseScraper
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from base_scraper import BaseScraper


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X profiles and posts."""
    
    @property
    def scraper_name(self) -> str:
        return "twitter_scraper"
    
    def scrape(self, start_date: str, end_date: str) -> None:
        """Scrape Twitter content for the given date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (inclusive)
            end_date: End date in YYYY-MM-DD format (inclusive)
        """
        config = self._load_source_config()
        url = config.get("source_client_key", {}).get("url")
        
        if not url:
            print(f"No URL found for {self.source_path.name}")
            return
        
        try:
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            
            raw_html = response.text
            content_hash = self._content_hash(raw_html)
            
            today_str = date.today().isoformat()
            
            if self._has_new_content(today_str, {content_hash}):
                print(f"New Twitter content found for {self.source_path.name}")
                filename = f"{self.source_path.stem}_{today_str}"
                self._save_content(today_str, filename, raw_html)
        except requests.RequestException as e:
            print(f"Error scraping Twitter {url}: {e}")
