#!/usr/bin/env python3
from feedparser import parse
from datetime import datetime, timedelta, timezone
import pytz

feed = parse('https://greenpointers.com/feed/')
est = pytz.timezone('America/New_York')
now = datetime.now(est)
print(f'Current time (EST): {now}')
yesterday_start = datetime(now.year, now.month, now.day - 1, tzinfo=timezone.utc)
yesterday_end = yesterday_start + timedelta(days=1)
print(f'Yesterday range: {yesterday_start} to {yesterday_end}')

# Check each entry's date
for i, entry in enumerate(feed.entries[:20]):
    pub_date_str = entry.get('published', 'N/A')
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6])
        print(f'Entry {i}: {dt.date()} - {entry.get("title", "N/A")[:50]}...')
