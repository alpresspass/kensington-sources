#!/usr/bin/env python3
"""
Scrape Brooklyn Community Board 12 news and meeting information.
CB12 covers Borough Park, Kensington (partially), Sunset Park, and Midwood.
"""

import argparse
from datetime import datetime, timedelta
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class CB12NewsItem(BaseModel):
    """A news item from Brooklyn Community Board 12."""
    title: str = Field(..., description="Title of the news/meeting")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    content_type: str = Field(..., description="Type: meeting, agenda, public_hearing, news")
    url: str = Field(..., description="URL to the source page or document")
    summary: Optional[str] = Field(None, description="Brief summary if available")


def parse_date_from_text(text: str) -> Optional[str]:
    """Extract date from meeting announcement text."""
    # Pattern for "Month Day" format like "January 27"
    months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    pattern = r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})'
    match = re.search(pattern, text.lower())
    
    if match:
        month = months.get(match.group(1), '01')
        day = match.group(2).zfill(2)
        year = datetime.now().year
        return f"{year}-{month}-{day}"
    
    return None


def fetch_cb12_news() -> List[CB12NewsItem]:
    """Fetch news and meeting information from CB12 website."""
    items = []
    base_url = "https://www.nyc.gov/site/brooklyncb12/index.page"
    
    try:
        with urllib.request.urlopen(base_url, timeout=30) as response:
            content = response.read().decode('utf-8')
        
        # Find meeting announcements
        # Pattern to find "Month Day" style dates in the page
        date_pattern = r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})'
        
        # Split content into sections and look for meeting info
        lines = content.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            if '##' in line or '<h2' in line.lower():
                if section_content:
                    process_section(current_section, ''.join(section_content), items)
                current_section = line.strip()
                section_content = [line]
            else:
                section_content.append(line)
        
        # Process last section
        if section_content:
            process_section(current_section, ''.join(section_content), items)
            
    except Exception as e:
        print(f"Error fetching CB12 news: {e}")
    
    return items


def process_section(title: str, content: str, items: List[CB12NewsItem]):
    """Process a section of the page to extract meeting/news info."""
    if not title or 'meeting' not in title.lower() and 'hearing' not in title.lower():
        return
    
    # Look for agenda PDF links
    agenda_pattern = r'/assets/brooklyncb12/downloads/pdf/([^\s"<>]+\.pdf)'
    matches = re.findall(agenda_pattern, content)
    
    for pdf_name in matches:
        # Extract month from filename like "1-January-2026-Agenda.pdf"
        month_match = re.search(r'(\d+)-(january|february|march|april|may|june|july|august|september|october|november|december)', pdf_name, re.IGNORECASE)
        if month_match:
            months = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12'
            }
            month = months.get(month_match.group(2).lower(), '01')
            day = month_match.group(1).zfill(2)
            year = datetime.now().year
            date_str = f"{year}-{month}-{day}"
            
            items.append(CB12NewsItem(
                title=f"CB12 {pdf_name.replace('.pdf', '').replace('-', ' ').title()} Agenda",
                date=date_str,
                content_type="agenda",
                url=f"https://www.nyc.gov{pdf_name}",
                summary="Community Board 12 meeting agenda"
            ))


def main():
    parser = argparse.ArgumentParser(description='Scrape Brooklyn Community Board 12 news')
    parser.add_argument('--date', type=str, help='Date to scrape (YYYY-MM-DD)', default=None)
    args = parser.parse_args()
    
    # Determine date range
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        target_date = datetime.now() - timedelta(days=1)
    
    start_time = datetime.now()
    log_entry = f"[{start_time.isoformat()}] Started scraping Brooklyn CB12 news for {target_date.strftime('%Y-%m-%d')}"
    print(log_entry)
    
    # Fetch news
    items = fetch_cb12_news()
    
    # Filter by date if specified
    filtered_items = []
    for item in items:
        try:
            item_date = datetime.strptime(item.date, '%Y-%m-%d')
            if args.date:
                if item_date == target_date:
                    filtered_items.append(item)
            else:
                # Get last full day's worth
                if item_date >= target_date - timedelta(days=7):
                    filtered_items.append(item)
        except:
            pass
    
    items = filtered_items
    
    # Create output directory for the date
    output_dir = Path(f"sources/brooklyn_cb12_news/data/{target_date.strftime('%Y-%m-%d')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save items
    if items:
        data_file = output_dir / "news.json"
        with open(data_file, 'w') as f:
            json.dump([item.model_dump() for item in items], f, indent=2)
        print(f"Saved {len(items)} news items to {data_file}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    log_entry = f"[{end_time.isoformat()}] Finished scraping. Found {len(items)} items in {duration:.1f}s"
    print(log_entry)
    
    # Update scrape_log.txt
    with open("sources/brooklyn_cb12_news/scrape_log.txt", "a") as log:
        log.write(f"{log_entry}\n")


if __name__ == '__main__':
    main()
