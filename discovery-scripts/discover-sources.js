const fetch = require('node-fetch');
const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

// RSS feeds to process
const rssFeeds = [
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
];

// Track discovered sources to avoid duplicates
const discoveredSources = new Set();
let sourceCount = 0;
const maxSources = 1000;

function extractExternalLinks(html, feedDomain) {
  const dom = new JSDOM(html);
  const links = dom.window.document.querySelectorAll('a');
  const externalLinks = new Set();
  
  links.forEach(link => {
    const href = link.href;
    try {
      const url = new URL(href);
      if (url.hostname !== feedDomain && !href.startsWith('#') && !href.startsWith('mailto:')) {
        externalLinks.add(href);
      }
    } catch (e) {}
  });
  
  return Array.from(externalLinks);
}

function categorizeSource(url, content = '') {
  const urlLower = url.toLowerCase();
  const contentLower = content.toLowerCase();
  
  // Government sources
  if (url.includes('.gov') || url.includes('nyc.gov') || url.includes('cityrecord')) {
    return 'government_website';
  }
  
  // NYC Open Data
  if (url.includes('opendata.nyc.gov') || url.includes('data.cityofnewyork.us')) {
    return 'nyc_open_data';
  }
  
  // Social media
  if (url.includes('facebook.com') || url.includes('instagram.com')) {
    return 'social_media';
  }
  if (url.includes('twitter.com') || url.includes('x.com')) {
    return 'social_media_twitter';
  }
  if (url.includes('linkedin.com')) {
    return 'social_media_linkedin';
  }
  
  // Real estate
  if (url.includes('streeteasy') || url.includes('zillow') || url.includes('realtor.com') || 
      url.includes('compass.com') || url.includes('corcoran')) {
    return 'real_estate_website';
  }
  
  // Business directories
  if (url.includes('yellowpages') || url.includes('yelp') || url.includes('maps.google')) {
    return 'business_directory';
  }
  
  // Schools/Education
  if (url.includes('.edu') || url.includes('schools.nyc.gov') || contentLower.includes('school')) {
    return 'educational_institution';
  }
  
  // News/Media
  if (url.includes('nytimes') || url.includes('nj.com') || url.includes('amny.com') ||
      url.includes('gothamist') || url.includes('brownstoner')) {
    return 'news_website';
  }
  
  // Community organizations
  if (contentLower.includes('community board') || contentLower.includes('nonprofit') || 
      contentLower.includes('ngo') || url.includes('.org')) {
    return 'community_organization';
  }
  
  // Default
  return 'website';
}

function determineAccessType(sourceType, url) {
  if (url.includes('opendata.nyc.gov') || url.includes('api.')) {
    return 'api_request';
  }
  if (url.includes('.gov')) {
    return 'website_page_scrape';
  }
  if (sourceType === 'social_media_twitter') {
    return 'twitter_api';
  }
  if (sourceType === 'social_media') {
    return 'facebook_graph_api';
  }
  return 'website_page_scrape';
}

function calculateValueScore(sourceType, url, content = '') {
  let score = 5; // Base score
  
  // Government sources are highly valuable
  if (sourceType === 'government_website') score += 3;
  if (sourceType === 'nyc_open_data') score += 4;
  
  // NYC-specific data is more relevant
  if (url.includes('nyc.gov') || url.includes('brooklyn')) score += 1;
  
  // Cap at 10
  return Math.min(score, 10);
}

function createSourceObject(url, feedUrl) {
  const sourceType = categorizeSource(url);
  const accessType = determineAccessType(sourceType, url);
  
  return {
    source_type: sourceType,
    source_access_type: accessType,
    source_client_key: {
      how_to_access: `Access via ${accessType}. URL: ${url}\nDiscovered from feed: ${feedUrl}`
    },
    value_score: calculateValueScore(sourceType, url),
    discovered_from: feedUrl
  };
}

async function fetchRssFeed(feedUrl) {
  try {
    const response = await fetch(feedUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.text();
  } catch (error) {
    console.error(`Failed to fetch ${feedUrl}:`, error.message);
    return null;
  }
}

async function processFeed(feedUrl) {
  console.log(`\nProcessing: ${feedUrl}`);
  
  const rssContent = await fetchRssFeed(feedUrl);
  if (!rssContent) return 0;
  
  // Parse RSS to extract article content and links
  const dom = new JSDOM(rssContent);
  const items = dom.window.document.querySelectorAll('item');
  
  let sourcesFound = 0;
  const feedDomain = new URL(feedUrl).hostname;
  
  for (const item of items) {
    if (sourceCount >= maxSources) break;
    
    // Get article content
    const description = item.querySelector('description')?.textContent || '';
    const link = item.querySelector('link')?.textContent || '';
    
    // Extract external links from description
    const externalLinks = extractExternalLinks(description, feedDomain);
    
    for (const extLink of externalLinks) {
      if (sourceCount >= maxSources) break;
      
      // Skip duplicates
      if (discoveredSources.has(extLink)) continue;
      
      discoveredSources.add(extLink);
      const source = createSourceObject(extLink, feedUrl);
      
      // Save source to file
      await saveSource(source);
      sourcesFound++;
      sourceCount++;
    }
  }
  
  console.log(`Found ${sourcesFound} new sources from this feed`);
  return sourcesFound;
}

async function saveSource(source) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const sourceName = `${source.source_type}_${timestamp}`;
  const filename = `${sourceName}.jsonl`;
  
  fs.writeFileSync(filename, JSON.stringify(source) + '\n');
  
  // Commit the file
  await execAsync(`git add ${filename}`);
  await execAsync(`git commit -m "fix: create ${sourceName} source"`);
  
  console.log(`Saved and committed: ${filename}`);
}

function execAsync(command) {
  return new Promise((resolve, reject) => {
    const { exec } = require('child_process');
    exec(command, (error, stdout, stderr) => {
      if (error) reject(error);
      else resolve(stdout);
    });
  });
}

async function main() {
  console.log(`Starting source discovery for Kensington, Brooklyn (11218)`);
  console.log(`Target: ${maxSources} sources`);
  
  for (const feed of rssFeeds) {
    if (sourceCount >= maxSources) break;
    await processFeed(feed);
  }
  
  console.log(`\nTotal sources discovered: ${sourceCount}`);
}

main().catch(console.error);
