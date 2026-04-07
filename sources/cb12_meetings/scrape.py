#!/usr/bin/env python3
"""
Scrape Brooklyn Community Board 12 meetings.
CB12 covers parts of Kensington (11218) along with Borough Park, Sunset Park, and Midwood.
Meetings are held every fourth Tuesday at 7pm (except July/August).
"""

import argparse
import sys
from datetime import date, datetime
import os
import re
import json

try:
    from models import CB12Meeting
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from models import CB12Meeting


def main():
    parser = argparse.ArgumentParser(description="Scrape CB12 Brooklyn Community Board meetings")
    parser.add_argument("--date", type=str, help="Date to scrape for (YYYY-MM-DD format)")
    args = parser.parse_args()
    
    from bs4 import BeautifulSoup
    import requests
    
    # Use the dedicated meetings page
    base_url = "https://www.nyc.gov/site/brooklyncb12/meetings/index.page"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(output_dir, "scrape_log.txt")
    
    start_time = datetime.now()
    print(f"[{start_time}] Starting CB12 meetings scrape from {base_url}...")
    
    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
        # Debug: Print raw HTML around "Tuesday"
        print("\n=== DEBUG: Raw HTML containing 'Tuesday' ===")
        if 'Tuesday' in html_content:
            idx = html_content.find('Tuesday')
            start_idx = max(0, idx - 200)
            end_idx = min(len(html_content), idx + 400)
            print(html_content[start_idx:end_idx])
        else:
            print("No 'Tuesday' found in HTML")
            # Print first 500 chars of body
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
            if body_match:
                print(f"\n=== First 1000 chars of body ===")
                print(body_match.group(1)[:1000])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_entry = f"[{start_time}] Started CB12 scrape -> [{end_time}] Finished ({duration:.1f}s)\n"
        
        with open(log_file, 'a') as f:
            f.write(log_entry)


if __name__ == "__main__":
    main()
