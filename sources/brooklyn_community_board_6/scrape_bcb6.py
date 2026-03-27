"""
Scrape Brooklyn Community Board 6 meeting minutes and agendas.

Community Board 6 covers Kensington, Bushwick, Bedford-Stuyvesant, East New York,
Cypress Hills, and parts of Brownsville. This is a primary source for:
- Zoning changes
- Liquor license applications
- Cannabis dispensary applications
- Building permits and variances
- Local development proposals
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import feedparser

# Add project root to path for models
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.community_board_meeting import CommunityBoardMeetingItem as CB6Model
from pydantic import BaseModel, Field


def parse_meeting_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats from CB6 website."""
    formats = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def is_kensington_relevant(title: str, topics: list[str] = None) -> bool:
    """
    Check if meeting content is relevant to Kensington area.
    
    Kensington-relevant keywords include neighborhood names, streets,
    and areas within or adjacent to CB6 that affect Kensington residents.
    """
    kensington_keywords = [
        # Neighborhoods
        'kensington', 'bushwick', 'bedford-stuyvesant', 'bed-stu',
        'east new york', 'cypress hills', 'brownsville',
        
        # Major streets in/near Kensington
        'myrtle avenue', 'knickerbocker avenue', 'flushing avenue',
        'jefferson street', 'st. marks avenue', 'rosevelt avenue',
        'norwood avenue', 'halsey street', 'emanuel street',
        
        # Cross-streets and areas
        'metropolitan avenue', 'nostrand avenue', 'jamaica avenue',
        'chester street', 'willoughby street',
        
        # General CB6 topics that affect Kensington
        'community board 6', 'cb6', 'brooklyn community board 6'
    ]
    
    title_lower = title.lower()
    
    # Check if any keyword is in the title
    for keyword in kensington_keywords:
        if keyword in title_lower:
            return True
    
    # Check topics if provided
    if topics:
        for topic in topics:
            topic_lower = topic.lower()
            for keyword in kensington_keywords:
                if keyword in topic_lower:
                    return True
    
    return False


def extract_topics_from_title(title: str) -> list[str]:
    """
    Extract potential topics from meeting title.
    
    This is a simple heuristic - real topic extraction would require
    parsing the actual meeting content/PDFs.
    """
    # Common topic indicators in titles
    topic_indicators = [
        'liquor license',
        'cannabis dispensary',
        'zoning change',
        'variance',
        'special permit',
        'building permit',
        'development proposal',
        'traffic calming',
        'parking study',
    ]
    
    title_lower = title.lower()
    found_topics = []
    
    for indicator in topic_indicators:
        if indicator in title_lower:
            found_topics.append(indicator)
    
    return found_topics


def scrape_cb6_meetings(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[CB6Model]:
    """
    Scrape meeting minutes and agendas from Brooklyn Community Board 6.
    
    Args:
        start_date: Start of date range (default: today)
        end_date: End of date range (default: yesterday)
    
    Returns:
        List of CB6Model objects
    """
    if start_date is None:
        start_date = datetime.now()
    if end_date is None:
        end_date = datetime.now() - timedelta(days=1)
    
    # CB6 uses a WordPress site with RSS feeds for meeting pages
    cb6_base_url = "https://brooklyncb6.cityofnewyork.us"
    
    # Meeting minutes page URL
    meeting_minutes_url = f"{cb6_base_url}/meeting-minutes/"
    
    items = []
    
    try:
        # Parse the meeting minutes page as RSS feed
        feed = feedparser.parse(meeting_minutes_url)
        
        for entry in feed.entries:
            # Get the date from the entry
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            else:
                continue
            
            # Filter by date range
            if not (start_date <= pub_date <= end_date):
                continue
            
            title = entry.title
            url = entry.link
            
            # Extract topics from title
            topics = extract_topics_from_title(title)
            
            # Check if Kensington-relevant
            if not is_kensington_relevant(title, topics):
                continue
            
            item = CB6Model(
                title=title,
                date=pub_date,
                url=url,
                content_type="minutes",
                topics=topics
            )
            items.append(item)
            
    except Exception as e:
        print(f"Error scraping CB6 meeting minutes: {e}")
    
    return items


def main():
    """Main entry point for scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Brooklyn Community Board 6 meetings")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    items = scrape_cb6_meetings(start_date, end_date)
    
    print(f"Found {len(items)} meeting items")
    for item in items:
        print(f"  - {item.date}: {item.title}")


if __name__ == "__main__":
    main()
