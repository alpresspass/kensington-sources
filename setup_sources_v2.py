"""Setup script to create folder structures and scrape_date.py scripts for all sources."""

import json
from pathlib import Path


def get_scraper_type(source_path: Path) -> str:
    """Determine the scraper type based on source name."""
    name = source_path.name.lower()
    
    if name.startswith("rss_") or "feed" in name:
        return "RSSFeedScraper"
    elif name.startswith("website_") or "community_" in name or "government_" in name:
        return "WebsiteScraper"
    else:
        return "WebsiteScraper"  # Default


def generate_scrape_script(source_path: Path, scraper_class: str) -> str:
    """Generate a scrape_date.py script for the given source."""
    
    return f'''#!/usr/bin/env python3
"""Scrape this source for a date range."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / ".." / "src"))

from {scraper_class} import {scraper_class}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape this source")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    # Get the source directory (parent of this script)
    source_path = Path(__file__).parent
    
    scraper = {scraper_class}(source_path)
    items = scraper.scrape(args.start_date, args.end_date)
    print(f"Scraped {{len(items)}} items from {{source_path.name}}")


if __name__ == "__main__":
    main()
'''


def main():
    """Main setup function."""
    workspace = Path(__file__).parent
    
    # Find all source directories
    source_dirs = [d for d in workspace.iterdir() 
                   if d.is_dir() and not d.name.startswith("src_")]
    
    print(f"Found {len(source_dirs)} sources")
    
    created = 0
    for source_path in sorted(source_dirs):
        scraper_class = get_scraper_type(source_path)
        script_content = generate_scrape_script(source_path, scraper_class)
        
        script_path = source_path / "scrape_date.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        created += 1
    
    print(f"Created {created} scrape scripts")


if __name__ == "__main__":
    main()
