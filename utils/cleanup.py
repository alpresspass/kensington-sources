#!/usr/bin/env python3
"""
Cleanup old scraped content to keep repository size manageable.
Keeps only the last N days of scraped data.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_scraped_content(days_to_keep=7):
    """Remove scraped content older than days_to_keep."""
    
    base_dir = Path(__file__).parent.parent
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    total_removed = 0
    total_size_freed = 0
    
    for source_dir in base_dir.iterdir():
        if not source_dir.is_dir():
            continue
            
        scraped_content_dir = source_dir / "scraped_content"
        if not scraped_content_dir.exists():
            continue
            
        for date_dir in scraped_content_dir.iterdir():
            if not date_dir.is_dir():
                continue
                
            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
            except ValueError:
                continue
            
            if dir_date < cutoff_date:
                # Calculate size before removing
                import shutil
                size = sum(f.stat().st_size for f in date_dir.rglob("*") if f.is_file())
                total_size_freed += size
                
                # Remove the directory
                import shutil
                shutil.rmtree(date_dir)
                total_removed += 1
                print(f"Removed: {date_dir} ({size / 1024:.1f} KB)")
    
    print(f"\nCleanup complete:")
    print(f"  Removed {total_removed} date directories")
    print(f"  Freed {total_size_freed / 1024 / 1024:.1f} MB")
    return total_removed

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Days of scraped content to keep")
    args = parser.parse_args()
    
    cleanup_old_scraped_content(args.days)

if __name__ == "__main__":
    main()
