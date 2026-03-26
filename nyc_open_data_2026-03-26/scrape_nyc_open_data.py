#!/usr/bin/env python3
"""
Scrape NYC Open Data API for Kensington-related datasets.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests

def scrape_nyc_open_data(output_dir: Path):
    """Fetch NYC Open Data datasets related to Brooklyn/Kensington."""
    
    base_url = "https://api.github.com/repos/NYCData/nyc-open-data/contents/datasets"
    
    # Search for relevant keywords
    keywords = ["brooklyn", "community board", "311", "complaints", "permits"]
    
    items = []
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    for keyword in keywords:
        search_url = f"https://api.github.com/search/code?q={keyword}+repo:NYCData/nyc-open-data"
        try:
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items.append({
                    "type": "search_result",
                    "keyword": keyword,
                    "count": data.get("total_count", 0),
                    "timestamp": timestamp
                })
        except Exception as e:
            print(f"Error searching for {keyword}: {e}")
    
    # Save results
    output_file = output_dir / f"nyc_open_data_{timestamp}.jsonl"
    with open(output_file, "w") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")
    
    return len(items)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    output_dir = base_dir / "scraped_content" / datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    count = scrape_nyc_open_data(output_dir)
    print(f"Scraped {count} items from NYC Open Data")

if __name__ == "__main__":
    main()
