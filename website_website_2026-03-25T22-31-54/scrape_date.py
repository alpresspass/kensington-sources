#!/usr/bin/env python3
"""Scrape this source for a date range."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / ".." / "src"))

from WebsiteScraper import WebsiteScraper


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape this source")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    # Get the source directory (parent of this script)
    source_path = Path(__file__).parent
    
    scraper = WebsiteScraper(source_path)
    items = scraper.scrape(args.start_date, args.end_date)
    print(f"Scraped {len(items)} items from {source_path.name}")


if __name__ == "__main__":
    main()
