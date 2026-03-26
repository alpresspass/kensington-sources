"""Main entry point to scrape all sources at once."""

import sys
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.website_scraper import WebsiteScraper
from src.rss_scraper import RSSFeedScraper


def get_scraper_for_source(source_path: Path) -> Union[WebsiteScraper, RSSFeedScraper, None]:
    """Determine the appropriate scraper for a source."""
    name = source_path.name.lower()
    
    if name.startswith("rss_") or "feed" in name:
        return RSSFeedScraper(source_path)
    elif name.startswith("website_") or "community_" in name or "government_" in name:
        return WebsiteScraper(source_path)
    else:
        # Default to website scraper
        return WebsiteScraper(source_path)


def scrape_source(source_path: Path, start_date: str, end_date: str) -> tuple[str, int]:
    """Scrape a single source and return (source_name, item_count)."""
    scraper = get_scraper_for_source(source_path)
    if not scraper:
        return (source_path.name, 0)
    
    items = scraper.scrape(start_date, end_date)
    return (source_path.name, len(items))


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Scrape all news sources")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--parallel", type=int, default=4, help="Number of parallel workers")
    args = parser.parse_args()
    
    # Validate dates
    try:
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
    except ValueError as e:
        print(f"Invalid date format: {e}")
        sys.exit(1)
    
    if start > end:
        print("Start date must be before or equal to end date")
        sys.exit(1)
    
    # Find all source directories
    workspace = Path(__file__).parent.parent
    source_dirs = [d for d in workspace.iterdir() 
                   if d.is_dir() and not d.name.startswith("src_")]
    
    print(f"Found {len(source_dirs)} sources to scrape")
    print(f"Date range: {args.start_date} to {args.end_date}")
    
    total_items = 0
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(scrape_source, d, args.start_date, args.end_date): d 
            for d in source_dirs
        }
        
        for future in as_completed(futures):
            source_name, item_count = future.result()
            if item_count > 0:
                successful += 1
                total_items += item_count
                print(f"✓ {source_name}: {item_count} items")
            else:
                failed += 1
    
    print(f"\nSummary: {successful}/{len(source_dirs)} sources scraped, {total_items} total items")


if __name__ == "__main__":
    main()
