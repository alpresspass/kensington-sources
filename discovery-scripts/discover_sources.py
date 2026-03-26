#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
import json
import subprocess
from datetime import datetime
from urllib.parse import urlparse
import os

# RSS feeds to process
RSS_FEEDS = [
    'https://greenpointers.com/feed',
    'https://www.6sqft.com/feed',
    'https://newyorkyimby.com/feed',
    'https://www.brooklynpaper.com/feed',
    'https://brooklyneagle.com/feed',
    'https://www.bkmag.com/feed',
    'https://canarsiecourier.com/feed',
    'https://northbrooklynnews.com/feed',
    'https://bushwickdaily.com/feed',
    'https://www.star-revue.com/feed',
    'https://brownstoner.com/feed',
    'https://www.amny.com/feed',
    'https://www.thecity.nyc/feed',
    'https://hellgatenyc.com/all-posts/rss/',
    'https://gothamist.com/feed',
    'https://www.boropark24.com/feed',
    'https://politicsny.com/feed/',
    'https://www.caribbeanlifenews.com/feed',
    'https://www.brooklynreporter.com/feed'
]

# Track discovered sources to avoid duplicates
discovered_sources = set()
source_count = 0
max_sources = 1000

def categorize_source(url):
    """Categorize a source based on its URL."""
    url_lower = url.lower()
    
    # Government sources
    if '.gov' in url or 'nyc.gov' in url:
        return 'government_website'
    
    # NYC Open Data
    if 'opendata.nyc.gov' in url or 'data.cityofnewyork.us' in url:
        return 'nyc_open_data'
    
    # Social media - Facebook/Instagram
    if 'facebook.com' in url or 'instagram.com' in url:
        return 'social_media'
    
    # Twitter/X
    if 'twitter.com' in url or 'x.com' in url:
        return 'social_media_twitter'
    
    # LinkedIn
    if 'linkedin.com' in url:
        return 'social_media_linkedin'
    
    # Real estate
    if any(x in url for x in ['streeteasy', 'zillow', 'realtor.com', 'compass.com']):
        return 'real_estate_website'
    
    # Business directories
    if any(x in url for x in ['yellowpages', 'yelp', 'maps.google']):
        return 'business_directory'
    
    # Schools/Education
    if '.edu' in url or 'schools.nyc.gov' in url:
        return 'educational_institution'
    
    # News/Media
    if any(x in url for x in ['nytimes.com', 'nj.com', 'amny.com']):
        return 'news_website'
    
    # Community organizations
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
    score = 5  # Base score
    
    # Government sources are highly valuable
    if source_type == 'government_website':
        score += 3
    if source_type == 'nyc_open_data':
        score += 4
    
    # NYC-specific data is more relevant
    if 'nyc.gov' in url or 'brooklyn' in url:
        score += 1
    
    return min(score, 10)

def extract_links_from_text(text):
    """Extract all URLs from text content."""
    import re
    urls = re.findall(r'https?://[^\s<>"]+', text)
    return [url.rstrip('/') for url in urls]

def parse_rss_feed(feed_url):
    """Parse an RSS feed and extract article content."""
    try:
        response = requests.get(feed_url, timeout=30)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Find all items (articles)
        items = root.findall('.//item')
        
        return items, urlparse(feed_url).netloc
    except Exception as e:
        print(f"  Error parsing {feed_url}: {e}")
        return [], None

def save_source(source_data):
    """Save a single source to a file and commit it."""
    global source_count
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
    source_type = source_data['source_type']
    source_name = f"{source_type}_{timestamp}"
    filename = f"{source_name}.jsonl"
    
    # Write to file
    with open(filename, 'w') as f:
        json.dump(source_data, f)
        f.write('\n')
    
    # Commit the file
    try:
        subprocess.run(['git', 'add', filename], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', f"fix: create {source_name} source"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}")
    
    print(f"  Saved: {filename} (type: {source_type}, score: {source_data['value_score']})")
    source_count += 1

def process_feed(feed_url):
    """Process a single RSS feed."""
    global source_count, discovered_sources
    
    print(f"\nProcessing: {feed_url}")
    
    if source_count >= max_sources:
        return
    
    items, feed_domain = parse_rss_feed(feed_url)
    
    if not items:
        print("  No items found or error parsing")
        return
    
    sources_found = 0
    
    for item in items:
        if source_count >= max_sources:
            break
        
        # Extract content from item
        description = item.find('description')
        content = description.text if description is not None else ''
        
        # Also check for encoded content
        encoded_content = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        if encoded_content is not None:
            content += ' ' + encoded_content.text
        
        # Extract links from content
        links = extract_links_from_text(content)
        
        for link in links:
            if source_count >= max_sources:
                break
            
            # Skip if already discovered
            if link in discovered_sources:
                continue
            
            # Skip internal links (same domain as feed)
            try:
                link_domain = urlparse(link).netloc
                if link_domain == feed_domain:
                    continue
            except:
                continue
            
            # Mark as discovered
            discovered_sources.add(link)
            
            # Create source data
            source_type = categorize_source(link)
            access_type = determine_access_type(source_type, link)
            value_score = calculate_value_score(source_type, link)
            
            source_data = {
                'source_type': source_type,
                'source_access_type': access_type,
                'source_client_key': {
                    'how_to_access': f"Access via {access_type}. URL: {link}\nDiscovered from feed: {feed_url}"
                },
                'value_score': value_score
            }
            
            save_source(source_data)
            sources_found += 1
    
    print(f"  Found {sources_found} new sources from this feed")
    return sources_found

def main():
    """Main function to process all feeds."""
    global source_count
    
    os.chdir('/Users/al/.openclaw/workspace/kensington-sources')
    
    print(f"Starting source discovery for Kensington, Brooklyn (11218)")
    print(f"Target: {max_sources} sources")
    print()
    
    total_found = 0
    for feed in RSS_FEEDS:
        if source_count >= max_sources:
            break
        found = process_feed(feed)
        total_found += found
    
    print(f"\n{'='*60}")
    print(f"Total sources discovered: {source_count}")
    print(f"Target reached: {'YES' if source_count >= max_sources else 'NO'}")

if __name__ == '__main__':
    main()
