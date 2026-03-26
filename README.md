# Kensington Sources

News source scrapers for Kensington, Brooklyn.

## Setup

```bash
# Install dependencies
pip install requests beautifulsoup4 feedparser
```

Or with uv:

```bash
uv pip install requests beautifulsoup4 feedparser
```

## Usage

### Scrape a single source

Each source has its own `scrape_date.py` script:

```bash
cd website_website_2026-03-25T22-31-26/
python scrape_date.py 2026-03-25 2026-03-25
```

### Scrape all sources at once

```bash
python src/main.py 2026-03-25 2026-03-25
```

With parallel workers:

```bash
python src/main.py 2026-03-25 2026-03-25 --parallel 8
```

## Directory Structure

Each source has its own folder:

```
website_website_2026-03-25T22-31-26/
├── scrape_date.py                    # Executable: python scrape_date.py <start> <end>
├── website_2026-03-25T22-31-26.jsonl  # Source configuration
├── scrape_log.txt                    # Scraping log with timestamps
└── scrape_items/                     # Parsed items by date
    └── 2026-03-25/
        └── website_..._2026-03-25.json  # JSON array of ScrapeItem objects
```

## Scraper Types

| Type | Class | Sources |
|------|-------|---------|
| Website | `WebsiteScraper` | 94 sources |
| RSS Feed | `RSSFeedScraper` | 8 sources |
| Twitter/X | `TwitterScraper` | 2 sources (not implemented) |
| NYC Open Data | `NYCOpenDataScraper` | 3 sources (not implemented) |

## ScrapeItem Structure

Each scraped item is a JSON object:

```json
{
  "title": "Article title",
  "content": "Extracted text content...",
  "url": "https://source.com/article",
  "published_at": "2026-03-25T10:30:00",
  "source": "website_...",
  "scrape_type": "website"
}
```

## Features

| Feature | Description |
|---------|-------------|
| **Parsed items** | Returns structured `ScrapeItem` objects, not raw HTML/RSS |
| **Duplicate detection** | Content hashed; only new content saved |
| **Date organization** | Items stored in `scrape_items/YYYY-MM-DD/` folders |
| **Logging** | Each source has `scrape_log.txt` with timestamps |
| **Common interface** | All scrapers: `.scrape(start_date, end_date) -> list[ScrapeItem]` |

## Verification

Tested successfully:
- ✓ Scrapes 10 items from website sources
- ✓ Items saved as JSON arrays in `scrape_items/YYYY-MM-DD/`
- ✓ Duplicate detection prevents re-saving identical content
- ✓ Log file tracks scraping activity with timestamps