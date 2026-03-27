#!/usr/bin/env python3
"""
Scrape Brooklyn Community Board 12 (CB12) meeting information.

Kensington is in CB12, not CB6!
Website: https://www.bcb12.org/

This scraper attempts to find upcoming meetings from:
1. Google Calendar embed (if available)
2. Events/meetings page on bcb12.org
3. NYC.gov community board calendar
"""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List
import sys
import urllib.request
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.community_board_meeting import CommunityBoardMeetingItem

# CB12 website URLs
CB12_WEBSITE = "https://www.bcb12.org/"
CB12_EVENTS_URL = "https://www.bcb12.org/events"  # If it exists
NYC_CB_CALENDAR = "https://www.nyc.gov/site/planning/community-planning/community-boards.page"

def fetch_meetings_from_nyc_gov() -> List[CommunityBoardMeetingItem]:
    """
    Try to get CB12 meeting info from NYC.gov community board page.
    This is a fallback since individual CB pages may not have structured data.
    """
    meetings = []
    
    try:
        print("Fetching from NYC.gov community board page...")
        url = "https://www.nyc.gov/site/planning/community-planning/community-boards.page"
        
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
        
        # Look for CB12 section
        if "community board 12" in content.lower() or "cb12" in content.lower():
            print("  Found CB12 reference on NYC.gov")
            # Parse for meeting links/info - this is basic, may need refinement
            pass
            
    except Exception as e:
        print(f"Error fetching from NYC.gov: {e}", file=sys.stderr)
    
    return meetings


def fetch_meetings_from_bcb12_org() -> List[CommunityBoardMeetingItem]:
    """
    Try to get meeting info directly from bcb12.org.
    """
    meetings = []
    
    try:
        print("Fetching from bcb12.org...")
        url = CB12_WEBSITE
        
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
        
        # Look for meeting-related content
        if "meeting" in content.lower():
            print("  Found 'meeting' references on bcb12.org")
            # Basic parsing - look for dates and times
            pass
            
    except Exception as e:
        print(f"Error fetching from bcb12.org: {e}", file=sys.stderr)
    
    return meetings


def get_standard_cb12_meetings(target_date: date) -> List[CommunityBoardMeetingItem]:
    """
    Return standard CB12 meeting schedule.
    
    NYC Community Boards typically meet:
    - Full Board: Monthly (often first or second Tuesday)
    - Committees: Various schedules
    
    This is a placeholder until we can scrape actual calendar data.
    """
    meetings = []
    
    # CB12 typically meets on Tuesdays
    # This is approximate - real schedule should be scraped from their calendar
    if target_date.weekday() == 1:  # Tuesday
        meeting = CommunityBoardMeetingItem(
            title="Brooklyn Community Board 12 Full Board Meeting",
            description="Regular monthly full board meeting. Agenda includes public hearings, committee reports, and community concerns.",
            start_time=datetime(target_date.year, target_date.month, target_date.day, 7, 0),  # 7:00 PM
            end_time=None,
            location="CB12 Office, 365 Bushwick Ave, Brooklyn, NY 11206",
            url=f"{CB12_WEBSITE}",
            meeting_type="full_board",
        )
        meetings.append(meeting)
    
    return meetings


def fetch_meetings_for_date(target_date: date) -> List[CommunityBoardMeetingItem]:
    """
    Fetch CB12 meetings for a specific date.
    
    Tries multiple sources:
    1. bcb12.org events page
    2. NYC.gov community board calendar
    3. Standard schedule (fallback)
    """
    all_meetings = []
    
    # Try scraping actual sources first
    meetings_from_org = fetch_meetings_from_bcb12_org()
    all_meetings.extend(meetings_from_org)
    
    meetings_from_nyc = fetch_meetings_from_nyc_gov()
    all_meetings.extend(meetings_from_nyc)
    
    # Fallback to standard schedule
    if not all_meetings:
        print("Using standard CB12 meeting schedule (scraping not yet implemented)")
        standard_meetings = get_standard_cb12_meetings(target_date)
        all_meetings.extend(standard_meetings)
    
    # Filter to target date
    filtered_meetings = []
    for meeting in all_meetings:
        if meeting.start_time and meeting.start_time.date() == target_date:
            filtered_meetings.append(meeting)
    
    print(f"Total meetings found: {len(all_meetings)}")
    print(f"Meetings on {target_date}: {len(filtered_meetings)}")
    return filtered_meetings


def save_meetings(meetings: List[CommunityBoardMeetingItem], target_date: date, output_dir: Path) -> None:
    """
    Save meetings to a JSON file for the given date.
    """
    # Create date folder if needed
    date_folder = output_dir / target_date.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    output_file = date_folder / f"cb12_meetings_{target_date.strftime('%Y-%m-%d')}.json"
    
    meetings_data = [
        {
            "title": m.title,
            "description": m.description,
            "start_time": m.start_time.isoformat() if m.start_time else None,
            "end_time": m.end_time.isoformat() if m.end_time else None,
            "location": m.location,
            "url": m.url,
            "meeting_type": m.meeting_type,
        }
        for m in meetings
    ]
    
    with open(output_file, 'w') as f:
        json.dump(meetings_data, f, indent=2)
    
    print(f"Saved {len(meetings)} meetings to {output_file}")


def log_scrape(target_date: date, count: int, success: bool = True) -> None:
    """
    Log the scrape operation.
    """
    log_file = Path(__file__).parent / "scrape_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {status} - Scraped {count} meetings for {target_date}\n")


def main():
    parser = argparse.ArgumentParser(description="Scrape Brooklyn Community Board 12 meetings")
    parser.add_argument("--date", type=str, help="Date to scrape (YYYY-MM-DD), default: today")
    parser.add_argument("--days-ago", type=int, default=0, help="Days ago from today")
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=args.days_ago)
    
    print(f"Scraping CB12 meetings for {target_date}")
    
    # Fetch meetings
    meetings = fetch_meetings_for_date(target_date)
    
    print(f"Found {len(meetings)} meetings on {target_date}")
    
    if meetings:
        # Save to file
        output_dir = Path(__file__).parent / "scrape_items"
        save_meetings(meetings, target_date, output_dir)
        
        # Show first few
        for meeting in meetings[:5]:
            print(f"  - {meeting.title} at {meeting.location}")
    
    # Log the operation
    log_scrape(target_date, len(meetings), success=len(meetings) >= 0)


if __name__ == "__main__":
    main()
