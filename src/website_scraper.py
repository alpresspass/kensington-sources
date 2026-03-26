"""Website scraper for news websites and general web pages."""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

# Handle both relative and absolute imports
try:
    from .base_scraper import BaseScraper, ScrapeItem
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from base_scraper import BaseScraper, ScrapeItem


class WebsiteScraper(BaseScraper):
    """Scraper for website pages."""
    
    @property
    def scraper_name(self) -> str:
        return "website_scraper"
    
    def scrape(self, start_date: str, end_date: str) -> list[ScrapeItem]:
        """Scrape website content for the given date range.
        
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
            # Extract URL from text like "Access via website_page_scrape. URL: https://..."
            if "URL:" in how_to_access:
                url = how_to_access.split("URL:")[-1].strip().split()[0]
        
        if not url:
            self._log(f"No URL found for {self.source_path.name}")
            return []
        
        # Parse dates
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        
        all_items: list[ScrapeItem] = []
        
        # Scrape the page (we scrape current state, not historical)
        try:
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            page_title = soup.title.string if soup.title else "Untitled"
            
            # Try to find article elements
            articles = []
            
            # Common selectors for news articles
            selectors = [
                'article',
                '.article', '.post', '.entry', '.story',
                '[class*="article"], [class*="post"], [class*="story"]',
                '[role="article"]'
            ]
            
            for selector in selectors:
                try:
                    found = soup.select(selector)
                    if found:
                        articles = found
                        break
                except Exception:
                    continue
            
            # If no articles found, use body as fallback
            if not articles:
                articles = [soup.find('body') or soup]
            
            today_str = date.today().isoformat()
            items_for_today: list[ScrapeItem] = []
            
            for i, article in enumerate(articles[:10]):  # Limit to first 10 articles
                title_elem = article.find(['h1', 'h2', 'h3', 'title'])
                title = (title_elem.get_text(strip=True) if title_elem else f"Article {i+1}")[:200]
                
                # Get content - try to find paragraph or use full text (limit size)
                content_elem = article.find(['p', 'div', 'span'])
                if not content_elem:
                    content_elem = article
                
                content = content_elem.get_text(strip=True)[:500]  # Reduced from 2000 to save space
                
                # Try to extract published date
                pub_date = None
                time_elem = article.find('time')
                if time_elem:
                    datetime_str = time_elem.get('datetime', '')
                    if datetime_str:
                        try:
                            pub_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        except ValueError:
                            pass
                
                item = ScrapeItem(
                    title=title,
                    content=content,
                    url=url,
                    published_at=pub_date,
                    source=self.source_path.name,
                    scrape_type="website"
                )
                items_for_today.append(item)
            
            all_items.extend(items_for_today)
            
            # Check if we have new items
            new_hashes = {self._item_hash(item) for item in items_for_today}
            if self._has_new_items(today_str, new_hashes):
                self._log(f"New items found for {self.source_path.name}: {len(items_for_today)} items")
                filename = f"{self.source_path.stem}_{today_str}"
                self._save_items(today_str, filename, items_for_today)
            
        except requests.RequestException as e:
            self._log(f"Error scraping {url}: {e}")
        
        return all_items
