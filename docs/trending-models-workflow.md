# Trending Models - Manual Workflow Guide

## Overview

The Trending Models feature allows you to discover and save popular 3D models from external platforms (MakerWorld and Printables) directly within Printernizer's Ideas section.

**Current Status**: Manual URL import workflow (fully functional)

## Quick Start

### Using the Manual Workflow

1. **Browse Trending Models** on external platforms:
   - MakerWorld: https://makerworld.com/en/models?sort=trend
   - Printables: https://www.printables.com/model?ordering=-popularity_score

2. **Copy Model URL** - Find an interesting model and copy its URL

3. **Import to Printernizer**:
   - Navigate to **Ideas** → **Bookmarks** tab
   - Click **"Import from URL"**
   - Paste the model URL
   - Add optional notes, tags, and mark as business/personal
   - Click **Save**

4. **Manage Imported Models**:
   - View in **Bookmarks** tab
   - Click "Open" to visit the original page
   - Click "Plan" to schedule for printing
   - Edit or delete as needed

## Supported Platforms

| Platform | URL Pattern | Trending Page |
|----------|------------|---------------|
| **MakerWorld** | `https://makerworld.com/en/models/*` | [Trending](https://makerworld.com/en/models?sort=trend) |
| **Printables** | `https://www.printables.com/model/*` | [Popular](https://www.printables.com/model?ordering=-popularity_score) |
| **Thingiverse** | `https://www.thingiverse.com/thing:*` | [Popular](https://www.thingiverse.com/explore/popular) |
| **MyMiniFactory** | `https://www.myminifactory.com/object/*` | [Trending](https://www.myminifactory.com/search/?query=&sortBy=popularity) |
| **Cults3D** | `https://cults3d.com/*` | [Popular](https://cults3d.com/en/tags/popular) |

## Features

### Automatic Metadata Extraction

When you import a URL, Printernizer automatically extracts:
- ✅ Model title
- ✅ Creator/author name
- ✅ Platform identification
- ✅ Thumbnail image (if available)
- ✅ Model description
- ✅ File information

### Organization

Imported models are automatically:
- Tagged with their source platform
- Categorized in the Bookmarks section
- Searchable and filterable
- Trackable through the print lifecycle (idea → planned → printing → completed)

## Future Enhancements

### Automatic Trending Discovery (Planned)

**Status**: Infrastructure in place, blocked by platform restrictions

**Background**:
- Both MakerWorld and Printables use Cloudflare bot protection
- Content is rendered client-side with JavaScript
- No public APIs are available for programmatic access

**Possible Solutions** (for future implementation):

#### Option 1: Browser Automation (Most Reliable)
- Use Playwright/Selenium to execute JavaScript
- Handles Cloudflare automatically
- Downloads ~50MB but works reliably
- **Estimated effort**: 2-4 hours

#### Option 2: Reverse-Engineer Internal APIs (Most Efficient)
- Inspect network traffic to find internal API endpoints
- Call them directly with proper headers
- Faster, no browser overhead
- May break if platforms change APIs
- **Estimated effort**: 4-8 hours + ongoing maintenance

#### Option 3: RSS/Feed Integration (If Available)
- Some platforms offer RSS feeds for trending content
- Simpler to implement
- Limited data compared to full scraping
- **Estimated effort**: 1-2 hours (if feeds exist)

### Recommended Next Steps

1. **Short term** (current): Continue using manual URL import
   - Works reliably
   - No maintenance overhead
   - User has full control

2. **Medium term** (when time allows): Implement browser automation
   - Set up Playwright in a background task
   - Run once daily to refresh trending cache
   - Display in dedicated "Trending" tab

3. **Long term**: Monitor for official APIs
   - Check if platforms release public APIs
   - Implement proper API integration
   - Most maintainable solution

## API Endpoints (for reference)

The following endpoints exist but are non-functional without proper scraping:

```http
# Get trending from all platforms
GET /api/v1/ideas/trending/all

# Get trending from specific platform
GET /api/v1/ideas/trending/makerworld
GET /api/v1/ideas/trending/printables

# Force refresh trending cache
POST /api/v1/ideas/trending/refresh

# Save trending item as personal idea
POST /api/v1/ideas/trending/{trending_id}/save
```

These endpoints will return empty results until automated scraping is implemented.

## Technical Notes

### Why Scraping Is Difficult

1. **Cloudflare Protection**: MakerWorld returns 403 Forbidden for automated requests
2. **JavaScript Rendering**: Both platforms load content dynamically with React/Vue
3. **No Public APIs**: Neither platform offers official programmatic access
4. **Rate Limiting**: Excessive requests may trigger IP bans

### Current Service Architecture

The `TrendingService` is enabled and initializes successfully, but:
- Background fetch tasks fail gracefully (logged, not displayed to user)
- No impact on application startup or performance
- Ready to be activated when scraping solution is implemented

### For Developers

If you want to implement automated trending discovery:

1. **Install Playwright** (for browser automation):
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Update TrendingService methods**:
   - `fetch_makerworld_trending()` - Add Playwright logic
   - `fetch_printables_trending()` - Add Playwright logic

3. **Test thoroughly**:
   - Verify Cloudflare bypass works
   - Check CSS selectors are correct
   - Handle pagination if needed
   - Add proper error handling

4. **Consider caching strategy**:
   - Current: 6-hour cache with background refresh
   - Adjust based on update frequency needs
   - Balance freshness vs. request volume

## Support

For questions or issues:
- GitHub Issues: https://github.com/schmacka/printernizer/issues
- Documentation: https://github.com/schmacka/printernizer/tree/master/docs

## Changelog

**v1.5.10** (2025-11-06)
- Re-enabled TrendingService infrastructure
- Fixed encoding detection bugs
- Documented manual workflow approach
- Prepared for future automation implementation
