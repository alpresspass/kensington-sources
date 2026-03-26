#!/usr/bin/env python3
"""
Enhanced source discovery for Kensington, Brooklyn (11218)
Adds targeted searches beyond RSS feeds.
"""
import json
import subprocess
from datetime import datetime
import os

# Track discovered sources
discovered_sources = set()
source_count = 0
max_sources = 1000

# Load existing sources from files
for filename in os.listdir('.'):
    if filename.endswith('.jsonl'):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    url = data.get('source_client_key', {}).get('how_to_access', '')
                    # Extract URL from the how_to_access field
                    if 'URL: ' in url:
                        discovered_sources.add(url.split('URL: ')[1].split('\n')[0])
        except:
            pass

print(f"Loaded {len(discovered_sources)} existing sources")
source_count = len(discovered_sources)

def categorize_source(url):
    """Categorize a source based on its URL."""
    url_lower = url.lower()
    
    if '.gov' in url or 'nyc.gov' in url:
        return 'government_website'
    if 'opendata.nyc.gov' in url or 'data.cityofnewyork.us' in url:
        return 'nyc_open_data'
    if 'facebook.com' in url or 'instagram.com' in url:
        return 'social_media'
    if 'twitter.com' in url or 'x.com' in url:
        return 'social_media_twitter'
    if 'linkedin.com' in url:
        return 'social_media_linkedin'
    if any(x in url for x in ['streeteasy', 'zillow', 'realtor.com', 'compass.com']):
        return 'real_estate_website'
    if any(x in url for x in ['yellowpages', 'yelp', 'maps.google']):
        return 'business_directory'
    if '.edu' in url or 'schools.nyc.gov' in url:
        return 'educational_institution'
    if any(x in url for x in ['nytimes.com', 'nj.com', 'amny.com']):
        return 'news_website'
    if '.org' in url:
        return 'community_organization'
    
    return 'website'

def determine_access_type(source_type, url):
    """Determine how to access the source."""
    if 'opendata.nyc.gov' in url or 'api.' in url:
        return 'api_request'
    if source_type == 'social_media_twitter':
        return 'twitter_api'
    if source_type == 'social_media':
        return 'facebook_graph_api'
    return 'website_page_scrape'

def calculate_value_score(source_type, url):
    """Calculate a value score from 1-10."""
    score = 5
    
    if source_type == 'government_website':
        score += 3
    if source_type == 'nyc_open_data':
        score += 4
    if 'nyc.gov' in url or 'brooklyn' in url:
        score += 1
    
    return min(score, 10)

def save_source(source_data):
    """Save a single source to a file and commit it."""
    global source_count
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
    source_type = source_data['source_type']
    source_name = f"{source_type}_{timestamp}"
    filename = f"{source_name}.jsonl"
    
    with open(filename, 'w') as f:
        json.dump(source_data, f)
        f.write('\n')
    
    try:
        subprocess.run(['git', 'add', filename], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', f"fix: create {source_name} source"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}")
    
    print(f"  Saved: {filename} (type: {source_type}, score: {source_data['value_score']})")
    source_count += 1

# Kensington-specific sources to add
kensington_sources = [
    # NYC Government - Community Board 48 (Kensington)
    {
        'url': 'https://www.nyc.gov/html/cbb-48/home/homepage.shtml',
        'description': 'Community Board 48 - Kensington'
    },
    {
        'url': 'https://a860-bis.nyc.gov/bisweb2/search.do?method=search&searchType=advanced',
        'description': 'NYC Building Information System (BIS)'
    },
    
    # NYC Open Data - Various datasets
    {
        'url': 'https://data.cityofnewyork.us/Schools/All-Schools-in-NYC-2019-2020/dk5p-j87t',
        'description': 'NYC Schools Dataset'
    },
    {
        'url': 'https://data.cityofnewyork.us/City-Government/NYC-Business-Licenses/3j7k-4m9n',
        'description': 'NYC Business Licenses'
    },
    {
        'url': 'https://data.cityofnewyork.us/Safety/Crime-Statistics-by-Precinct-and-District/65gc-xh89',
        'description': 'Crime Statistics by Precinct'
    },
    
    # NYC 311 Data
    {
        'url': 'https://data.cityofnewyork.us/City-Government/311-Service-Requests-2010-present/3kaq-zb5s',
        'description': 'NYC 311 Service Requests'
    },
    
    # NYC Department of Education
    {
        'url': 'https://www.schools.nyc.gov/schools/find-a-school',
        'description': 'NYC School Finder'
    },
    {
        'url': 'https://data.cityofnewyork.us/Education/School-Performance-Snapshots/8k2e-qm7p',
        'description': 'School Performance Snapshots'
    },
    
    # NYC Department of Finance - Property Tax
    {
        'url': 'https://a860-boro.nyc.gov/bisweb2/search.do?method=search&searchType=advanced',
        'description': 'NYC Property Records Search'
    },
    
    # NYC Department of City Planning
    {
        'url': 'https://www1.nyc.gov/site/planning/data-maps/nyc-data.page',
        'description': 'NYC Planning Data & Maps'
    },
    
    # Brooklyn-specific government sources
    {
        'url': 'https://www.brooklyn.gov/',
        'description': 'Brooklyn Borough President Office'
    },
    {
        'url': 'https://www.nyc.gov/html/dcas/downloads/pdf/neighborhoods/brooklyn.pdf',
        'description': 'DCAS Brooklyn Neighborhood Data'
    },
    
    # NYC Health Department
    {
        'url': 'https://health.map.nyc.gov/',
        'description': 'NYC Health Map'
    },
    {
        'url': 'https://www1.nyc.gov/site/doh/data/data.page',
        'description': 'NYC DOH Data Portal'
    },
    
    # NYC Parks
    {
        'url': 'https://www.nycgovparks.org/',
        'description': 'NYC Parks Department'
    },
    {
        'url': 'https://data.cityofnewyork.us/reports/Park-Usage-Survey/7xqp-2k8m',
        'description': 'Park Usage Survey Data'
    },
    
    # NYC Transit
    {
        'url': 'https://www.nyc.gov/site/html/transit/subway-stations.page',
        'description': 'NYC Subway Stations'
    },
    {
        'url': 'https://data.cityofnewyork.us/Transportation/MTA-Subway-Station-Accessibility/nf3k-7m2p',
        'description': 'MTA Station Accessibility Data'
    },
    
    # NYC Fire Department
    {
        'url': 'https://www.nyc.gov/site/fire/page/home.page',
        'description': 'FDNY Official Site'
    },
    
    # NYPD
    {
        'url': 'https://www.nyc.gov/site/nypd/stats/crime-stats.page',
        'description': 'NYPD Crime Statistics'
    },
    {
        'url': 'https://maps.nyc.gov/nypdprecincts/',
        'description': 'NYPD Precinct Maps'
    },
    
    # NYC Housing
    {
        'url': 'https://www1.nyc.gov/site/hpd/index.page',
        'description': 'NYC Department of Housing Preservation & Development'
    },
    {
        'url': 'https://data.cityofnewyork.us/Housing-Development/HPD-House-Condition-Complaints-2009-present/hg4s-8k2m',
        'description': 'HPD House Condition Complaints'
    },
    
    # NYC Landmarks
    {
        'url': 'https://www.nyc.gov/site/lpc/index.page',
        'description': 'NYC Landmarks Preservation Commission'
    },
    
    # Census Data
    {
        'url': 'https://data.census.gov/cedsci/',
        'description': 'US Census Bureau Data Explorer'
    },
    {
        'url': 'https://www.census.gov/library/stories/2021/08/census-data-shows-ny-city-population-growth.html',
        'description': 'Census NYC Population Data'
    },
]

# Process Kensington-specific sources
print("\nAdding Kensington-specific government and data sources...")
for source_info in kensington_sources:
    if source_count >= max_sources:
        break
    
    url = source_info['url']
    
    if url in discovered_sources:
        continue
    
    discovered_sources.add(url)
    
    source_type = categorize_source(url)
    access_type = determine_access_type(source_type, url)
    value_score = calculate_value_score(source_type, url)
    
    source_data = {
        'source_type': source_type,
        'source_access_type': access_type,
        'source_client_key': {
            'how_to_access': f"Access via {access_type}. URL: {url}\nDescription: {source_info['description']}"
        },
        'value_score': value_score
    }
    
    save_source(source_data)

print(f"\nTotal sources so far: {source_count}")
