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
    
    base_url = "https://www.nyc.gov/site/brooklyncb12/index.page"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(output_dir, "scrape_log.txt")
    
    start_time = datetime.now()
    print(f"[{start_time}] Starting CB12 meetings scrape...")
    
    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        all_text = soup.get_text()
        
        # Pattern to find meeting blocks:
        # "Tuesday, January 27 at 7:00 PM" followed by "January Board Meeting"
        pattern = r'(Tuesday, \w+ \d+ at \d+:\d+ [AP]M)\s+(\w+ Board Meeting)'
        
        matches = re.findall(pattern, all_text)
        print(f"\nFound {len(matches)} meeting patterns")
        
        meetings = []
        scraped_on = date.today()
        
        for match in matches:
            meeting_date_str = match[0]
            month_name = match[1].split()[0]  # Extract "January" from "January Board Meeting"
            print(f"  - {meeting_date_str}: {month_name} Board Meeting")
            
            meeting = CB12Meeting(
                meeting_date=meeting_date_str,
                month_name=month_name,
                agenda_url=None,  # Will need separate extraction
                zoom_url=None,
                scraped_on=scraped_on
            )
            meetings.append(meeting)
        
        print(f"\nTotal: {len(meetings)} meetings")
        
        # Save meetings to JSON file
        date_str = args.date or date.today().isoformat()
        output_file = os.path.join(output_dir, f"meetings_{date_str}.json")
        
        with open(output_file, 'w') as f:
            json.dump([m.model_dump() for m in meetings], f, indent=2)
        print(f"Saved to {output_file}")
        
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
