#!/bin/bash

cd /Users/al/.openclaw/workspace/kensington-sources

# RSS feeds to process
FEEDS=(
  "https://greenpointers.com/feed"
  "https://www.6sqft.com/feed"
  "https://newyorkyimby.com/feed"
  "https://www.brooklynpaper.com/feed"
  "https://brooklyneagle.com/feed"
  "https://www.bkmag.com/feed"
  "https://canarsiecourier.com/feed"
  "https://northbrooklynnews.com/feed"
  "https://bushwickdaily.com/feed"
  "https://www.star-revue.com/feed"
  "https://brownstoner.com/feed"
  "https://www.amny.com/feed"
  "https://www.thecity.nyc/feed"
  "https://hellgatenyc.com/all-posts/rss/"
  "https://gothamist.com/feed"
  "https://www.boropark24.com/feed"
  "https://politicsny.com/feed/"
  "https://www.caribbeanlifenews.com/feed"
  "https://www.brooklynreporter.com/feed"
)

# Track discovered sources
declare -A DISCOVERED_SOURCES
SOURCE_COUNT=0
MAX_SOURCES=1000

# Function to categorize a source URL
categorize_source() {
  local url="$1"
  
  # Government sources
  if [[ "$url" == *".gov"* ]] || [[ "$url" == *"nyc.gov"* ]]; then
    echo "government_website"
    return
  fi
  
  # NYC Open Data
  if [[ "$url" == *"opendata.nyc.gov"* ]] || [[ "$url" == *"data.cityofnewyork.us"* ]]; then
    echo "nyc_open_data"
    return
  fi
  
  # Social media - Facebook/Instagram
  if [[ "$url" == *"facebook.com"* ]] || [[ "$url" == *"instagram.com"* ]]; then
    echo "social_media"
    return
  fi
  
  # Twitter/X
  if [[ "$url" == *"twitter.com"* ]] || [[ "$url" == *"x.com"* ]]; then
    echo "social_media_twitter"
    return
  fi
  
  # LinkedIn
  if [[ "$url" == *"linkedin.com"* ]]; then
    echo "social_media_linkedin"
    return
  fi
  
  # Real estate
  if [[ "$url" == *"streeteasy"* ]] || [[ "$url" == *"zillow"* ]] || [[ "$url" == *"realtor.com"* ]]; then
    echo "real_estate_website"
    return
  fi
  
  # Business directories
  if [[ "$url" == *"yellowpages"* ]] || [[ "$url" == *"yelp"* ]] || [[ "$url" == *"maps.google"* ]]; then
    echo "business_directory"
    return
  fi
  
  # Schools/Education
  if [[ "$url" == *".edu"* ]] || [[ "$url" == *"schools.nyc.gov"* ]]; then
    echo "educational_institution"
    return
  fi
  
  # News/Media
  if [[ "$url" == *"nytimes.com"* ]] || [[ "$url" == *"nj.com"* ]] || [[ "$url" == *"amny.com"* ]]; then
    echo "news_website"
    return
  fi
  
  # Community organizations
  if [[ "$url" == *".org"* ]]; then
    echo "community_organization"
    return
  fi
  
  echo "website"
}

# Function to determine access type
determine_access_type() {
  local source_type="$1"
  local url="$2"
  
  if [[ "$url" == *"opendata.nyc.gov"* ]] || [[ "$url" == *"api."* ]]; then
    echo "api_request"
    return
  fi
  
  if [[ "$source_type" == "social_media_twitter" ]]; then
    echo "twitter_api"
    return
  fi
  
  if [[ "$source_type" == "social_media" ]]; then
    echo "facebook_graph_api"
    return
  fi
  
  echo "website_page_scrape"
}

# Function to calculate value score
calculate_value_score() {
  local source_type="$1"
  local url="$2"
  
  local score=5
  
  # Government sources are highly valuable
  [[ "$source_type" == "government_website" ]] && ((score += 3))
  [[ "$source_type" == "nyc_open_data" ]] && ((score += 4))
  
  # NYC-specific data is more relevant
  [[ "$url" == *"nyc.gov"* ]] || [[ "$url" == *"brooklyn"* ]] && ((score += 1))
  
  # Cap at 10
  echo $(( score > 10 ? 10 : score ))
}

# Function to save a single source
save_source() {
  local url="$1"
  local feed_url="$2"
  
  local timestamp=$(date -u +"%Y-%m-%dT%H-%M-%S")
  local source_type=$(categorize_source "$url")
  local access_type=$(determine_access_type "$source_type" "$url")
  local value_score=$(calculate_value_score "$source_type" "$url")
  
  # Create unique name
  local source_name="${source_type}_${timestamp}"
  local filename="${source_name}.jsonl"
  
  # Escape URL for JSON
  local escaped_url=$(echo "$url" | sed 's/\\/\\\\/g; s/"/\\"/g')
  local escaped_feed=$(echo "$feed_url" | sed 's/\\/\\\\/g; s/"/\\"/g')
  
  # Create JSON content
  cat > "$filename" << EOF
{"source_type":"${source_type}","source_access_type":"${access_type}","source_client_key":{"how_to_access":"Access via ${access_type}. URL: ${escaped_url}\nDiscovered from feed: ${escaped_feed}"},"value_score":${value_score}}
EOF
  
  # Commit the file
  git add "$filename"
  git commit -m "fix: create ${source_name} source" > /dev/null 2>&1
  
  echo "Saved: $filename (type: $source_type, score: $value_score)"
}

# Function to extract external links from RSS content
extract_links() {
  local rss_content="$1"
  local feed_domain="$2"
  
  # Extract all href values and filter for external links
  echo "$rss_content" | grep -oP 'href="[^"]+"' | sed 's/href="//g; s/"//g' | while read -r link; do
    # Skip internal links, anchors, mailto, etc.
    [[ "$link" == "#"* ]] && continue
    [[ "$link" == "mailto:"* ]] && continue
    [[ "$link" == "tel:"* ]] && continue
    
    # Check if it's an external link (different domain)
    if [[ "$link" == http* ]]; then
      local link_domain=$(echo "$link" | sed -E 's|https?://([^/]+).*|\1|')
      if [[ "$link_domain" != "$feed_domain" ]]; then
        echo "$link"
      fi
    fi
  done
}

# Main processing loop
echo "Starting source discovery for Kensington, Brooklyn (11218)"
echo "Target: $MAX_SOURCES sources"
echo ""

for feed in "${FEEDS[@]}"; do
  if (( SOURCE_COUNT >= MAX_SOURCES )); then
    break
  fi
  
  echo "Processing: $feed"
  
  # Fetch RSS feed
  rss_content=$(curl -s "$feed" 2>/dev/null)
  
  if [[ -z "$rss_content" ]]; then
    echo "  Failed to fetch feed, skipping..."
    continue
  fi
  
  # Get feed domain
  feed_domain=$(echo "$feed" | sed -E 's|https?://([^/]+).*|\1|')
  
  # Extract and process links
  extract_links "$rss_content" "$feed_domain" | sort -u | while read -r link; do
    if (( SOURCE_COUNT >= MAX_SOURCES )); then
      break
    fi
    
    # Skip if already discovered
    if [[ -n "${DISCOVERED_SOURCES[$link]}" ]]; then
      continue
    fi
    
    DISCOVERED_SOURCES["$link"]=1
    save_source "$link" "$feed"
    ((SOURCE_COUNT++))
  done
  
  echo "Sources found so far: $SOURCE_COUNT"
done

echo ""
echo "Total sources discovered: $SOURCE_COUNT"
