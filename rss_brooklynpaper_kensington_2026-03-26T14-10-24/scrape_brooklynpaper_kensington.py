#!/usr/bin/env python3
"""Brooklyn Paper Kensington RSS Feed Scraper"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rss_scraper import RSSFeedScraper

def main():
    scraper = RSSFeedScraper(
        source_path=Path('rss_brooklynpaper_kensington_2026-03-26T14-10-24')
    )
    scraper.run()

if __name__ == '__main__':
    main()
