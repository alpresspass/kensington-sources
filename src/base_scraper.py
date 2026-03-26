"""Base scraper class with common interface for all scrapers."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional


class ScrapeItem:
    """Represents a single scraped item (article, event, post, etc.)."""
    
    def __init__(self, title: str, content: str, url: str = "", 
                 published_at: Optional[datetime] = None, **metadata):
        self.title = title
        self.content = content  # Raw or extracted text
        self.url = url
        self.published_at = published_at or datetime.now()
        self.metadata = metadata
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            **self.metadata
        }
    
    def __hash__(self) -> int:
        """Hash based on title + content for duplicate detection."""
        return hash(f"{self.title}:{self.content[:100]}")


class BaseScraper(ABC):
    """Abstract base class defining the scraper interface.
    
    All scrapers must implement this interface:
    - scrape(start_date: str, end_date: str) -> None
      Scrapes content for the given date range and stores it in
      scraped_content/<date>/ folders. Only creates folders if new
      unique content is found.
    """
    
    def __init__(self, source_path: Path):
        """Initialize scraper with source directory path."""
        self.source_path = Path(source_path)
        self.scraped_content_dir = self.source_path / "scrape_items"
        self.log_file = self.source_path / "scrape_log.txt"
        self._ensure_directories()
    
    def _log(self, message: str) -> None:
        """Append a timestamped log entry."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _ensure_directories(self) -> None:
        """Create scrape_items directory if it doesn't exist."""
        self.scraped_content_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def scrape(self, start_date: str, end_date: str) -> list[ScrapeItem]:
        """Scrape content for the given date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (inclusive)
            end_date: End date in YYYY-MM-DD format (inclusive)
            
        Returns:
            List of ScrapeItem objects found
            
        Items are stored in scrape_items/<date>/ folders.
        Only creates a folder if new unique items are found for that day.
        """
        pass
    
    def _item_hash(self, item: ScrapeItem) -> str:
        """Generate hash of item to detect duplicates."""
        return hashlib.sha256(f"{item.title}:{item.content[:500]}".encode()).hexdigest()
    
    def _has_new_items(self, date_str: str, new_hashes: set[str]) -> bool:
        """Check if any new unique items exist for a date.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            new_hashes: Set of hashes from newly scraped items
            
        Returns:
            True if there's content that doesn't exist yet
        """
        day_dir = self.scraped_content_dir / date_str
        if not day_dir.exists():
            return True
            
        existing_hashes = set()
        for file in day_dir.iterdir():
            if file.is_file() and file.suffix == '.json':
                with open(file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    for item in items:
                        existing_hashes.add(self._item_hash_from_dict(item))
                    
        return not new_hashes.issubset(existing_hashes)
    
    def _item_hash_from_dict(self, item_dict: dict) -> str:
        """Generate hash from a dictionary representation."""
        title = item_dict.get('title', '')
        content = item_dict.get('content', '')[:500]
        return hashlib.sha256(f"{title}:{content}".encode()).hexdigest()
    
    def _save_items(self, date_str: str, filename: str, items: list[ScrapeItem]) -> None:
        """Save scraped items to a JSON file.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            filename: Name of the file (without extension)
            items: List of ScrapeItem objects
        """
        day_dir = self.scraped_content_dir / date_str
        day_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = day_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([item.to_dict() for item in items], f, indent=2)
    
    def _load_source_config(self) -> dict:
        """Load the source configuration from JSONL file."""
        # Find the JSONL config file
        for f in self.source_path.iterdir():
            if f.suffix == '.jsonl':
                with open(f, 'r') as fp:
                    line = fp.readline()
                    return json.loads(line)
        return {}
    
    @property
    def scraper_name(self) -> str:
        """Return the name of this scraper."""
        return self.__class__.__name__