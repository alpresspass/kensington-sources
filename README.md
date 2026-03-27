# Kensington Free Press - Primary Source Repository

This repository contains **primary source** scrapers for the **Kensington Free Press (KFP)**, covering Kensington, Brooklyn (zip code 11218).

## Overview

The KFP collects news from **primary sources only** — NOT news publications. We use news sites like Greenpointers to *discover* real sources, but never scrape them directly.

### What Counts as a Primary Source?

✅ **YES - Primary Sources:**
- Community Board meeting minutes and agendas (CB6 covers Kensington)
- NYC building permits and zoning applications
- Liquor license applications (NYC ABC)
- Cannabis dispensary applications
- Traffic route changes, parking studies
- Government press releases and alerts
- Subreddit posts from local communities
- Event calendars from community organizations

❌ **NO - Not Primary Sources:**
- News publications (Greenpointers, Brooklyn Eagle, 6sqft, etc.)
- Blog posts about local news
- Any site that reports on events rather than being the source

Each source is organized in its own folder under `sources/` with a consistent interface.

## Directory Structure

```
kensington-sources/
├── README.md                    # This file
├── models/                      # Pydantic ScrapeItem models
│   ├── __init__.py             # Model exports
│   ├── base.py                 # BaseScrapeItem, SourceMetadata
│   ├── rss_item.py             # RSSArticleItem model
│   ├── event_item.py           # EventItem model  
│   ├── alert_item.py           # AlertItem model
│   └── subreddit_post.py       # SubredditPostItem model
├── sources/                     # Individual source folders
│   ├── greenpointers_rss/
│   │   ├── scrape_greenpointers.py    # Executable scraper script
│   │   ├── scrape_log.txt             # Scraping activity log
│   │   └── scrape_items/              # ScrapeItems organized by date
│   │       └── 2026-03-25/
│   │           └── *.json             # Individual ScrapeItem files
│   ├── mta_alerts/
│   ├── brooklyn_eagle_rss/
│   └── ...
└── story_leads/               # Daily curated stories (generated at 11pm EST)
    └── 2026-03-25/
        └── *.md                    # Story summaries with sources
```

## Quality Source Criteria

Sources must meet these criteria:

1. **Updated regularly** - Active content updates
2. **Not a news publication itself** - Use publications like Greenpointers to *find* sources, not scrape them directly as primary sources
3. **Can produce headlines** - Content must be scrapable into KFP headlines
4. **Relevant to Kensington (11218)** - Geographic or topical relevance

### Good Sources Examples:
- `https://mta.info/alerts` - Individual service change alerts → "G Trains not running past Church Ave"
- Subreddits like r/KensingtonBrooklyn, r/Greenpoint, r/Williamsburg, r/Brooklyn, r/Flatbush
- Community organization event calendars
- NYC Open Data feeds for local area

### Avoid:
- Scraping homepages of government sites (scrape specific pages instead)
- News publications as primary sources (use them to discover real sources)

## RSS Feeds for Source Discovery

Use these RSS feeds to find new sources:

```python
RSS_FEEDS = [
    "https://greenpointers.com/feed",
    "https://www.6sqft.com/feed",
    "https://newyorkyimby.com/feed",
    "https://www.brooklynpaper.com/feed",
    "https://brooklyneagle.com/feed",
    "https://www.bkmag.com/feed",
    "https://canarsiecourier.com/feed",
    "https://northbrooklynnews.com/feed",
    "https://bushwickdaily.com/feed",
    "https://www.star-revue.com/feed",
    "https://brownstoner.com/feed",
    "https://www.amny.com/feed",
    "https://www.thecity.nyc/feed",
    "https://hellgatenyc.com/all-posts/rss/",
    "https://gothamist.com/feed",
    "https://www.boropark24.com/feed",
    "https://politicsny.com/feed/",
    "https://www.caribbeanlifenews.com/feed",
    "https://www.brooklynreporter.com/feed"
]
```

## Usage

### Scrape a Single Source

Each source has an executable Python script with consistent interface:

```bash
cd sources/greenpointers_rss/

# Scrape all available content
uv run scrape_greenpointers.py

# Scrape last full day only (12:01am EST → 11:59pm)
uv run scrape_greenpointers.py --last-day

# Scrape since a specific date
uv run scrape_greenpointers.py --since 2026-03-20
```

### Common Interface

All scraper scripts support:
- `--last-day` - Only the last full day
- `--since YYYY-MM-DD` - Items since specified date

## ScrapeItem Models

Each source type has a Pydantic model in `models/`:

```python
from models import RSSArticleItem, EventItem, AlertItem, SubredditPostItem

# Example RSS article item
item = RSSArticleItem(
    id="abc123",
    title="New Development Proposed in Kensington",
    link="https://example.com/article",
    summary="Brief description...",
    content=None,
    published_at=datetime.now(),
    author="John Doe",
    categories=["development", "kensington"]
)

# Check if item can produce a headline
if item.can_produce_headline():
    print(f"Headline: {item.title}")
```

### Model Types

| Model | Source Type | Example |
|-------|-------------|----------|
| `RSSArticleItem` | RSS feeds | Greenpointers, Brooklyn Eagle |
| `AlertItem` | Service alerts | MTA service changes |
| `EventItem` | Calendar events | Community board meetings |
| `SubredditPostItem` | Reddit posts | r/KensingtonBrooklyn |

## Daily Story Leads Generation

At **11pm EST** each day, the system should:

1. Read through all sources collected during the day
2. Find 5-10 most interesting and best-corroborated stories (multiple sources)
3. Create `story_leads/YYYY-MM-DD/` folder with markdown files
4. Each story file includes:
   - Summary of the story
   - List of supporting sources
   - Why it's important to Kensington

## Setup

```bash
# Install dependencies with uv
uv pip install requests beautifulsoup4 feedparser python-dateutil
```

Or with pip:

```bash
pip install requests beautifulsoup4 feedparser python-dateutil
```

## Features

| Feature | Description |
|---------|-------------|
| **Parsed items** | Returns structured `ScrapeItem` Pydantic models |
| **Date organization** | Items stored in `scrape_items/YYYY-MM-DD/` folders |
| **Duplicate detection** | Content hashed; only new content saved |
| **Logging** | Each source has `scrape_log.txt` with timestamps |
| **Consistent interface** | All scrapers support `--last-day` and `--since` arguments |

## Maintenance Tasks

### During Heartbeats (2-4 times per day)

1. ✅ Check existing sources have up-to-date ScrapeItem folders via `scrape_log.txt`
2. ✅ Update scripts that may be out of date
3. ✅ Note any API keys needed in Git issues/README
4. ✅ Find new relevant sources for Kensington (11218)
5. ✅ Remove low-value sources (e.g., scraped homepage instead of press release page)

### Daily at 11pm EST

- Generate story leads from day's collected content
- Identify best-corroborated stories with multiple sources

## Notes

- **Commit frequently** - Source information must be committed to GitHub often to avoid losing work
- **One source per folder** - If a site has multiple sources (e.g., Reddit), each subreddit gets its own folder
- **Scrape specific pages** - Don't scrape `mta.info` homepage; scrape `mta.info/alerts` for actionable alerts

---

*Repository: https://github.com/alpresspass/kensington-sources*
