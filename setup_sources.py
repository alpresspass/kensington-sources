#!/usr/bin/env python3
"""Setup script to reorganize sources into folders with scrape_date scripts."""

import json
from pathlib import Path

WORKSPACE = Path("/Users/al/.openclaw/workspace/kensington-sources")

def get_scraper_type(source_config: dict) -> str:
    """Determine the scraper type based on source configuration."""
    source_type = source_config.get("source_type", "")
    access_type = source_config.get("source_access_type", "")
    
    if "rss" in access_type.lower() or "feed" in access_type.lower():
        return "rss_feed_scraper"
    elif "twitter" in source_type.lower():
        return "twitter_scraper"
    elif "nyc_open_data" in source_type.lower():
        return "nyc_opendata_scraper"
    else:
        return "website_scraper"

def create_source_folder(source_path: Path) -> Path:
    """Create a folder structure for a single source."""
    # Read the JSONL file
    with open(source_path, 'r') as f:
        config = json.loads(f.readline())
    
    # Create folder name from source type and stem
    source_type = config.get("source_type", "unknown")
    folder_name = f"{source_type}_{source_path.stem}"
    new_folder = WORKSPACE / folder_name
    
    # Create directory structure
    new_folder.mkdir(exist_ok=True)
    (new_folder / "scraped_content").mkdir(exist_ok=True)
    
    # Copy the JSONL file
    import shutil
    shutil.copy(source_path, new_folder / f"{source_path.name}")
    
    # Determine scraper type
    scraper_type = get_scraper_type(config)
    
    # Create scrape_date.py script
    scrape_script = new_folder / "scrape_date.py"
    create_scrape_script(scrape_script, scraper_type, folder_name)
    
    return new_folder

def create_scrape_script(script_path: Path, scraper_type: str, source_name: str) -> None:
    """Create a scrape_date.py script for the given source."""
    
    # Map module names to class names
    class_map = {
        "website_scraper": "WebsiteScraper",
        "rss_feed_scraper": "RSSFeedScraper", 
        "twitter_scraper": "TwitterScraper",
        "nyc_opendata_scraper": "NYCOpenDataScraper",
    }
    class_name = class_map.get(scraper_type)
    if not class_name:
        # Fallback: capitalize each word
        parts = scraper_type.replace("_scraper", "").split("_")
        class_name = "".join(part.capitalize() for part in parts) + "Scraper"
        if "Feed" not in class_name and "feed" in scraper_type:
            class_name = class_name.replace("Scrape", "Feed")
    
    script_content = f'''#!/usr/bin/env python3
"""Scrape content for {source_name}.

Usage:
    python scrape_date.py <start_date> <end_date>
    
Example:
    python scrape_date.py 2026-01-01 2026-01-31
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from {scraper_type} import {class_name}


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {{Path(__file__).name}} <start_date> <end_date>")
        print("Example: python scrape_date.py 2026-01-01 2026-01-31")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    # Get the source directory (where this script lives)
    source_path = Path(__file__).parent
    
    # Create and run scraper
    scraper = {class_name}(source_path)
    scraper.scrape(start_date, end_date)


if __name__ == "__main__":
    main()
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    script_path.chmod(0o755)

def main():
    """Main setup function."""
    # Find all JSONL files in workspace root
    jsonl_files = list(WORKSPACE.glob("*.jsonl"))
    
    print(f"Found {len(jsonl_files)} source files")
    
    for source_path in jsonl_files:
        new_folder = create_source_folder(source_path)
        print(f"Created: {new_folder.name}")
    
    print("\nSetup complete!")

if __name__ == "__main__":
    main()
