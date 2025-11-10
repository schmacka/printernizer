# 3D Model Platform API Research

**Research Date**: 2025-11-10
**Purpose**: Explore API availability for integrating 3D model search from popular platforms into Printernizer

## Executive Summary

Three major 3D model platforms were evaluated for API integration potential:

| Platform | Official API | Search Available | Recommendation |
|----------|-------------|------------------|----------------|
| **Thingiverse** | ✅ Yes | ✅ Yes | **Best option** - Full REST API with search |
| **Printables** | ❌ No | 🟡 Possible | Reverse engineer GraphQL endpoint |
| **MakerWorld** | ❌ No | 🔴 Difficult | Requires scraping or paid services |

---

## 1. Thingiverse

### Status: ✅ READY FOR INTEGRATION

### Overview
- **Official API**: REST API with comprehensive documentation
- **Documentation**: https://www.thingiverse.com/developers
- **Swagger Docs**: https://www.thingiverse.com/developers/swagger
- **Authentication**: OAuth2 with app registration
- **Rate Limits**: Unknown (check docs)

### Authentication Setup

1. Create app at: https://www.thingiverse.com/apps/create
2. Get: Client ID, Client Secret, App Token
3. OAuth flow for user authorization
4. Use access token for API requests

### Search Capabilities

**Keyword Search**:
- Endpoint method: `keyword_search(term)`
- Base URL: `https://api.thingiverse.com/search/{term}`
- Query params: `?access_token={token}&per_page={limit}`

**Browse/Discovery**:
- Newest: `GET /newest`
- Popular: `GET /popular`
- Featured: `GET /featured`
- By Category: `GET /categories/{slug}`
- By Tag: `GET /tags/{tag}/things`

### Available Data

For each "Thing" (model):
- Basic info: name, description, slug, URL
- Creator: username, avatar, profile
- Metrics: likes, downloads, views, makes
- Files: STL, 3MF, GCODE with download URLs
- Images: thumbnails, preview images
- Metadata: tags, categories, license
- Dates: created, modified, published

### Python Integration Example

```python
from thingiverse import Thingiverse

# Initialize with access token
tv = Thingiverse(token='your_access_token')

# Search for models
results = tv.keyword_search('calibration cube')

# Get model details
thing = tv.get_thing('1234567')
print(f"Name: {thing['name']}")
print(f"Creator: {thing['creator']['name']}")
print(f"Likes: {thing['like_count']}")
print(f"Downloads: {thing['download_count']}")

# Get file URLs
files = tv.get_thing_file('1234567', None)
for file in files:
    print(f"File: {file['name']} - {file['download_url']}")
```

### JavaScript/Node.js Example

```javascript
const thingiverse = require('thingiverse-js');

// Search
thingiverse('search/calibration', {
  token: 'your_token',
  query: { per_page: 20 }
})
.then(res => {
  res.body.hits.forEach(thing => {
    console.log(`${thing.name} by ${thing.creator.name}`);
  });
})
.catch(err => console.error(thingiverse.getError(err.response)));

// Get thing details
thingiverse('things/1234567', { token: 'your_token' })
  .then(res => console.log(res.body));
```

### API Libraries

- **Python**: https://github.com/bonnee/thingiverse
- **Node.js**: https://github.com/makerbot/thingiverse-js (archived but functional)
- **Ruby**: https://github.com/makerbot/thingiverse-ruby

### Complete API Methods

**Thing Operations**:
- `get_thing(thing_id)` - Get model details
- `get_thing_files(thing_id)` - List downloadable files
- `get_thing_images(thing_id)` - Get preview images
- `get_thing_likes(thing_id)` - Get like count/users
- `get_thing_copies(thing_id)` - Get "makes"
- `get_thing_tags(thing_id)` - Get tags
- `get_thing_category(thing_id)` - Get category
- `get_thing_zip(thing_id)` - Download all files as ZIP

**Search & Discovery**:
- `keyword_search(term)` - Text search
- `get_newest_things()` - Recent uploads
- `get_popular_things()` - Trending models
- `get_featured_things()` - Editorial picks
- `get_categories(slug)` - Browse by category
- `get_latest_category(category)` - Recent in category
- `get_latest_tag(tag)` - Recent with tag

**User Operations**:
- `get_profile(username)` - User profile
- `get_things_user(username)` - User's models
- `get_likes_user(username)` - User's likes
- `get_collections_user(username)` - User's collections

### Integration Considerations

**Pros**:
- Official, stable API
- Comprehensive search functionality
- Rich metadata and file access
- Active community, multiple libraries
- No scraping needed

**Cons**:
- OAuth2 setup required
- Rate limits may apply
- Platform stability concerns (Makerbot ownership)
- Some API docs outdated

---

## 2. Printables (Prusa)

### Status: 🟡 POSSIBLE WITH REVERSE ENGINEERING

### Overview
- **Official API**: None (requested by community, not delivered)
- **Unofficial Access**: GraphQL endpoint exists
- **Documentation**: None official
- **Authentication**: Unknown (likely session-based)

### Community Solutions

**PrintablesGraphQL Library**:
- Repository: https://github.com/100prznt/PrintablesGraphQL
- Languages: PHP, JavaScript
- Status: Minimal documentation
- Purpose: "Simple implementation to get print details"

### Available Data (via GraphQL)

Based on PrintablesGraphQL library:
- Model info: slug, name, description
- User data: id, username, avatar, level, print count
- Engagement: ratings, shares, likes, makes, downloads
- Media: image files and paths
- License information
- Thingiverse links (for cross-posted models)

### GraphQL Endpoint

**Suspected endpoint**: `https://api.printables.com/graphql` (not confirmed)

The site uses GraphQL internally, which can be reverse-engineered:
1. Open browser DevTools on printables.com
2. Monitor Network tab for GraphQL requests
3. Inspect query structure and endpoints
4. Extract authentication method

### Search Capabilities

**Status**: Not documented in PrintablesGraphQL

The site has search functionality, so GraphQL queries likely exist for:
- Text search
- Filter by category
- Filter by user
- Sort by popular/newest/makes

Would require reverse engineering the web app's GraphQL queries.

### Integration Approach

```javascript
// Hypothetical example (needs verification)
const query = `
  query SearchModels($term: String!, $limit: Int) {
    search(term: $term, limit: $limit) {
      items {
        id
        slug
        name
        description
        likesCount
        downloadsCount
        images {
          filePath
        }
        user {
          username
          avatar
        }
      }
    }
  }
`;

fetch('https://api.printables.com/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    // Auth headers if needed
  },
  body: JSON.stringify({
    query: query,
    variables: { term: 'calibration', limit: 20 }
  })
});
```

### Integration Considerations

**Pros**:
- Growing platform (Prusa backing)
- Quality models from community
- GraphQL is structured and efficient
- No OAuth complexity

**Cons**:
- No official API or documentation
- Reverse engineering required
- Endpoint/schema may change without notice
- Possible ToS violation
- Authentication method unclear
- No community libraries for search

**Community Feedback**:
- Forum users requesting API since 2021
- Prusa team response: "Would assist very few and increase curation work"
- Some users resort to Playwright automation
- No timeline for official API

---

## 3. MakerWorld (Bambu Lab)

### Status: 🔴 NOT RECOMMENDED

### Overview
- **Official API**: None
- **Documentation**: None
- **Access Method**: Web scraping only
- **Platform**: JavaScript-heavy React application

### Challenges

**Technical Barriers**:
- JavaScript-rendered content (hard to scrape)
- No GraphQL endpoint found
- Traditional scraping tools fail
- Constantly evolving UI

**Community Discussion**:
- Forum thread: https://forum.bambulab.com/t/scrape-website-data-api/113401
- Users reporting scraping difficulties
- No official API plans announced

### Third-Party Scraping Services

**Apify MakerWorld Scraper**:
- Service: https://apify.com/lexis-solutions/maker-world-com
- Type: Commercial web scraper
- Pricing: Pay-per-use (Apify platform)
- OpenAPI: Available

**Features**:
- Extract model metadata
- Creator profiles
- Download statistics
- Likes, downloads, boosts
- Images and thumbnails
- Certification status
- Fan/follower counts

**Automatio.ai Scraper**:
- Service: https://automatio.ai/templates/en/makerworld-web-scraper-and-api
- Type: Automation platform
- Similar capabilities to Apify

### Integration Considerations

**Pros**:
- Bambu Lab's official model library
- Growing collection
- Tight integration with Bambu printers

**Cons**:
- No API (official or unofficial)
- Requires paid scraping services
- Unreliable (site changes break scrapers)
- Possible ToS violations
- Rate limiting/blocking risks
- No search query control
- Maintenance burden

**Recommendation**: Wait for official API or avoid integration

---

## Integration Recommendations for Printernizer

### Recommended Approach: Phased Implementation

#### Phase 1: Thingiverse Integration (MVP)
**Priority**: HIGH
**Effort**: LOW-MEDIUM
**Risk**: LOW

**Implementation**:
1. Create Thingiverse OAuth app
2. Add API credentials to Printernizer config
3. Implement search service using Python thingiverse library
4. Add search endpoint to Printernizer API
5. Build simple search UI in frontend
6. Display results with thumbnails, creator, stats
7. Provide links to Thingiverse for downloads

**Benefits**:
- Proven, stable API
- Rich search capabilities
- Direct file download URLs available
- Large model library
- Quick to implement

#### Phase 2: Printables Integration (Optional)
**Priority**: MEDIUM
**Effort**: MEDIUM-HIGH
**Risk**: MEDIUM

**Prerequisites**:
- Reverse engineer GraphQL endpoint
- Document query structure
- Test authentication requirements
- Verify ToS compliance

**Implementation**:
1. Capture GraphQL queries from browser
2. Create custom GraphQL client
3. Add Printables search to multi-source search
4. Handle potential breaking changes

**Benefits**:
- Access to Prusa community models
- High-quality, print-tested designs
- Complementary to Thingiverse

**Risks**:
- Unofficial API may break
- ToS concerns
- Maintenance overhead

#### Phase 3: MakerWorld (Future)
**Priority**: LOW
**Effort**: HIGH
**Risk**: HIGH

**Approach**: Wait for official API

**Interim Option**: If critical, consider:
- Commercial scraper API (Apify)
- Budget for ongoing costs
- Accept reliability issues

### Suggested Feature Set

**Basic Search Interface**:
```
┌─────────────────────────────────────┐
│ Search 3D Models                    │
│ ┌─────────────────────────────────┐ │
│ │ calibration cube            [🔍] │ │
│ └─────────────────────────────────┘ │
│ Source: [x] Thingiverse [ ] Printables
└─────────────────────────────────────┘

Results:
┌────────────────────────────────────┐
│ 📦 [Image] Calibration Cube XYZ    │
│    by MakerUser123                 │
│    ❤️ 1.2k  ⬇️ 5.4k  👁️ 12k        │
│    [View on Thingiverse]           │
└────────────────────────────────────┘
```

**Key Features**:
- Text search across platforms
- Filter by platform
- Sort by popular/newest/makes
- Display thumbnails
- Show creator and stats
- Link to platform for download
- Optional: Save to favorites/library

**Database Schema Addition**:
```python
class ExternalModel(Base):
    """Track external 3D models from platforms"""
    id: int
    platform: str  # 'thingiverse', 'printables', 'makerworld'
    platform_id: str  # External platform ID
    name: str
    description: str
    creator: str
    thumbnail_url: str
    model_url: str
    download_url: Optional[str]
    likes: int
    downloads: int
    created_at: datetime
    cached_at: datetime  # When we cached this data
```

### API Endpoint Design

```python
# src/api/routers/external_models.py

@router.get("/search")
async def search_external_models(
    query: str,
    platforms: List[str] = Query(default=["thingiverse"]),
    limit: int = 20,
    sort: str = "popular"
):
    """
    Search for 3D models across external platforms

    Platforms: thingiverse, printables (if available)
    Sort: popular, newest, likes, downloads
    """
    pass

@router.get("/{platform}/{model_id}")
async def get_external_model_details(
    platform: str,
    model_id: str
):
    """Get detailed information about a specific external model"""
    pass
```

### Service Architecture

```python
# src/services/external_models_service.py

class ExternalModelsService:
    """Manage searches across 3D model platforms"""

    def __init__(self):
        self.thingiverse = ThingiverseClient(
            token=config.THINGIVERSE_TOKEN
        )
        self.printables = PrintablesClient() if available

    async def search(
        self,
        query: str,
        platforms: List[str],
        limit: int
    ) -> List[ExternalModel]:
        """Search across specified platforms"""
        results = []

        if "thingiverse" in platforms:
            results.extend(
                await self.search_thingiverse(query, limit)
            )

        if "printables" in platforms:
            results.extend(
                await self.search_printables(query, limit)
            )

        return self.merge_and_sort(results, limit)
```

---

## Security & Legal Considerations

### API Terms of Service

**Thingiverse**:
- Review API ToS before implementation
- Respect rate limits
- Attribute content properly
- Don't redistribute files without permission

**Printables**:
- No official API = no official ToS
- Use GraphQL responsibly if implementing
- Respect rate limits
- Risk of access being blocked

**MakerWorld**:
- Web scraping likely violates ToS
- Commercial scrapers may have agreements
- Not recommended for production

### Data Caching

**Best Practices**:
- Cache search results with TTL (e.g., 1 hour)
- Store only metadata, not files
- Update cache on user request
- Respect robots.txt
- Don't hammer APIs

### Attribution

**Requirements**:
- Display creator names
- Link to original platform
- Show platform logos/badges
- Include license information
- Don't claim content as your own

---

## Implementation Timeline

### Week 1-2: Thingiverse Integration
- Set up OAuth app and credentials
- Implement API client wrapper
- Create search service
- Add API endpoints
- Basic testing

### Week 3: Frontend Development
- Design search UI
- Implement search interface
- Display results with thumbnails
- Link to external platforms
- Handle errors gracefully

### Week 4: Testing & Refinement
- End-to-end testing
- Rate limit handling
- Error scenarios
- Performance optimization
- Documentation

### Future: Printables (if pursued)
- Reverse engineer GraphQL (1-2 weeks)
- Implement client (1 week)
- Integration testing (1 week)
- Monitor for breaking changes (ongoing)

---

## Technical Resources

### Thingiverse
- Official Docs: https://www.thingiverse.com/developers
- REST API Reference: https://www.thingiverse.com/developers/rest-api-reference
- Swagger: https://www.thingiverse.com/developers/swagger
- Python Wrapper: https://github.com/bonnee/thingiverse
- Node.js Wrapper: https://github.com/makerbot/thingiverse-js
- Examples: https://gist.github.com/HarlemSquirrel/0be679d756b1391a61919f2b03699201

### Printables
- Community Request: https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/printables-application-programmable-interface-api/
- PrintablesGraphQL: https://github.com/100prznt/PrintablesGraphQL
- GraphQL Guide: https://graphql.org/learn/

### MakerWorld
- Forum Discussion: https://forum.bambulab.com/t/scrape-website-data-api/113401
- Apify Scraper: https://apify.com/lexis-solutions/maker-world-com
- Automatio Scraper: https://automatio.ai/templates/en/makerworld-web-scraper-and-api

---

## Next Steps

1. **Validate Requirements**: Confirm with stakeholders that external model search is desired
2. **Test Thingiverse API**: Create test app and validate search capabilities
3. **Design UI/UX**: Mockup search interface integration
4. **Estimate Effort**: Detailed sprint planning
5. **Legal Review**: Verify ToS compliance
6. **Implement MVP**: Start with Thingiverse integration
7. **Gather Feedback**: Test with users before expanding
8. **Evaluate Printables**: Decide if reverse engineering is worth the effort
9. **Monitor MakerWorld**: Watch for official API announcements

---

## Conclusion

**Thingiverse provides the clearest path to integration** with its official REST API, comprehensive search capabilities, and available libraries. This should be the starting point for any external model search feature in Printernizer.

Printables is technically possible but requires reverse engineering and carries maintenance risks. Consider only after Thingiverse integration is stable and user feedback justifies the additional effort.

MakerWorld integration should be avoided until an official API is released, as scraping solutions are unreliable and potentially problematic.

The recommended approach is to **start with Thingiverse as an MVP**, validate user demand for external model search, and expand to other platforms based on feedback and API availability.
