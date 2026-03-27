#!/usr/bin/env python3
"""
Scrape NYC DOB Building Permit data filtered for Kensington area.

NYC Open Data source:
https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Approved-Permits/rbx6-tga4

This dataset has REAL-TIME data with current permits issued today/yesterday.
Uses CSV endpoint (more reliable than JSON API).
"""

import argparse
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List
import sys
import urllib.request

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.building_permit import BuildingPermitItem


# Kensington zip code - covers the neighborhood and surrounding area
KENSINGTON_ZIP_CODE = "11218"

# NYC Open Data CSV endpoint - REAL-TIME dataset!
CSV_URL = "https://data.cityofnewyork.us/resource/rbx6-tga4.csv"


def is_in_kensington_area(zip_code: str) -> bool:
    """
    Check if a zip code matches Kensington (11218).
    """
    return zip_code == KENSINGTON_ZIP_CODE


def fetch_permits_for_date(target_date: date) -> List[BuildingPermitItem]:
    """
    Fetch building permits for a specific date.
    
    Downloads full CSV and filters by zip code 11218 (Kensington area) in Python.
    Uses rbx6-tga4 dataset which has REAL-TIME data (not historical like ipu4-2q9a).
    """
    # Format date as NYC Open Data expects (YYYY-MM-DD)
    target_date_str = target_date.strftime("%Y-%m-%d")
    
    permits = []
    zip_code_count = 0
    kensington_count = 0
    
    try:
        print(f"Fetching DOB permits for {target_date_str}")
        print(f"  Zip Code: {KENSINGTON_ZIP_CODE}")
        
        # Download CSV
        with urllib.request.urlopen(CSV_URL, timeout=60) as response:
            content = response.read().decode('utf-8')
        
        # Parse CSV
        reader = csv.DictReader(content.splitlines())
        
        for row in reader:
            # Filter by zip code (Kensington area)
            row_zip_code = row.get("zip_code", "")
            if not is_in_kensington_area(row_zip_code):
                continue
            zip_code_count += 1
            
            # Check issued date matches target (format: YYYY-MM-DD)
            issued_date = row.get("issued_date", "")
            if issued_date != target_date_str:
                continue
            
            try:
                permit = BuildingPermitItem(
                    permit_number=row.get("job_filing_number", ""),  # job_filing_number is the permit number
                    job_type=row.get("work_type", ""),
                    building_class=None,  # Not in this dataset
                    block=int(row["block"]) if row.get("block") else 0,
                    lot=int(row["lot"]) if row.get("lot") else 0,
                    borough="4",  # Brooklyn code
                    house_number=row.get("house__") or None,
                    street_name=row.get("street_name") or None,
                    zip_code=row.get("zip_code") or None,
                    work_type=row.get("work_type") or None,
                    permit_issued_date=target_date,
                    expiration_date=None,  # Not in this dataset
                    estimated_cost=None,  # Not in this dataset
                )
                permits.append(permit)
            except (KeyError, ValueError) as e:
                continue  # Skip malformed rows
        
        print(f"  Zip code {KENSINGTON_ZIP_CODE} permits: {zip_code_count}")
        print(f"  Total permits found: {len(permits)}")
        return permits
        
    except Exception as e:
        print(f"Error fetching permits: {e}", file=sys.stderr)
        return []


def save_permits(permits: List[BuildingPermitItem], target_date: date, output_dir: Path) -> None:
    """
    Save permits to a JSON file for the given date.
    """
    # Create date folder if needed
    date_folder = output_dir / target_date.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    output_file = date_folder / f"dob_permits_{target_date.strftime('%Y-%m-%d')}.json"
    
    permits_data = [
        {
            "permit_number": p.permit_number,
            "job_type": p.job_type,
            "building_class": p.building_class,
            "block": p.block,
            "lot": p.lot,
            "borough": p.borough,
            "house_number": p.house_number,
            "street_name": p.street_name,
            "zip_code": p.zip_code,
            "work_type": p.work_type,
            "permit_issued_date": p.permit_issued_date.isoformat(),
            "expiration_date": p.expiration_date.isoformat() if p.expiration_date else None,
            "estimated_cost": p.estimated_cost,
        }
        for p in permits
    ]
    
    with open(output_file, 'w') as f:
        json.dump(permits_data, f, indent=2)
    
    print(f"Saved {len(permits)} permits to {output_file}")


def log_scrape(target_date: date, count: int, success: bool = True) -> None:
    """
    Log the scrape operation.
    """
    log_file = Path(__file__).parent / "scrape_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {status} - Scraped {count} permits for {target_date}\n")


def main():
    parser = argparse.ArgumentParser(description="Scrape NYC DOB building permits for Kensington")
    parser.add_argument("--date", type=str, help="Date to scrape (YYYY-MM-DD), default: today")
    parser.add_argument("--days-ago", type=int, default=0, help="Days ago from today")
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=args.days_ago)
    
    print(f"Scraping DOB permits for {target_date}")
    
    # Fetch permits
    permits = fetch_permits_for_date(target_date)
    
    print(f"Found {len(permits)} permits in Kensington area")
    
    if permits:
        # Save to file
        output_dir = Path(__file__).parent / "scrape_items"
        save_permits(permits, target_date, output_dir)
        
        # Show first few
        for permit in permits[:5]:  # Show first 5
            address = f"{permit.house_number or ''} {permit.street_name or ''}".strip()
            print(f"  - Permit {permit.permit_number}: {permit.job_type} at {address}")
    
    # Log the operation
    log_scrape(target_date, len(permits), success=len(permits) >= 0)


if __name__ == "__main__":
    main()
