# Ideas Section - Feature Specification

## Overview

The Ideas Section is a comprehensive feature for Printernizer that provides a centralized hub for managing print ideas, bookmarking models from external platforms (Makerworld and Printables), and discovering trending 3D models. This feature bridges the gap between inspiration and execution in 3D printing workflows.

## Vision Statement

Create an integrated ideas management system that allows users to:
- Capture and organize print ideas before execution
- Bookmark interesting models from popular 3D printing platforms
- Discover trending models for inspiration
- Seamlessly transition ideas into actual print jobs
- Distinguish between business and personal projects for proper tracking

## Feature Scope

### Phase 1 - MVP Features

#### 1. Personal Ideas Management

**Core Functionality:**
- Create, Read, Update, Delete (CRUD) operations for ideas
- Rich idea details including title, description, estimated print time, and priority
- Categorization system with custom tags (gift, prototype, product, decoration)
- Status workflow: Idea → Planned → Printing → Completed → Archived
- Business/Personal classification for accounting integration
- Free-form notes field for requirements, materials, and customer information

**Data Fields:**
- `title` (required): Name of the idea
- `description`: Detailed description of the project
- `category`: User-defined categories
- `priority`: 1-5 scale (5 being highest)
- `status`: Current state in the workflow
- `is_business`: Boolean flag for business tracking
- `estimated_print_time`: Hours/minutes estimate
- `material_notes`: Specific material requirements
- `customer_info`: For business orders
- `planned_date`: Target execution date
- `completed_date`: Actual completion date

#### 2. External Model Bookmarks

**Supported Platforms:**
- Makerworld (Bambu Lab's platform)
- Printables (Prusa's platform)

**Features:**
- Manual URL import via paste
- Automatic metadata extraction:
  - Model title
  - Creator information
  - Thumbnail image
  - File count
  - Download count/likes (if available)
- Local thumbnail caching for offline viewing
- Print status tracking (bookmarked/downloaded/printed)
- Quick action buttons:
  - Download to printer folder
  - Add to print queue
  - Open on platform

**Storage Strategy:**
- Store only metadata and thumbnails locally
- Maintain platform URLs for direct access
- No automatic file downloads (manual trigger only)

#### 3. Trending Discovery

**Content Sources:**
- Daily trending from Makerworld
- Weekly trending from Printables
- Category-based filtering (functional, artistic, toys, tools)

**Implementation:**
- Background job for periodic updates (configurable interval)
- Local caching with TTL (Time To Live)
- Thumbnail grid display with hover details
- One-click save to personal ideas
- Platform attribution and creator credits

**Cache Strategy:**
- Update trending every 6 hours
- Store last 100 trending items per platform
- Automatic cleanup of expired cache entries

### Phase 2 - Future Enhancements

- **Account Integration**: OAuth-based sync with Makerworld/Printables accounts
- **Cost Estimation**: Automatic material and time cost calculations
- **Bulk Operations**: Queue multiple ideas for batch printing
- **Collections**: Group related ideas into projects
- **Sharing**: Export/share idea collections
- **AI Features**: Similar model recommendations based on history
- **Templates**: Reusable idea templates for common projects

## Technical Architecture

### Database Schema

```sql
-- Ideas table
CREATE TABLE ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    source_type TEXT CHECK(source_type IN ('manual', 'makerworld', 'printables')),
    source_url TEXT,
    thumbnail_path TEXT,
    category TEXT,
    priority INTEGER CHECK(priority BETWEEN 1 AND 5),
    status TEXT CHECK(status IN ('idea', 'planned', 'printing', 'completed', 'archived')),
    is_business BOOLEAN DEFAULT FALSE,
    estimated_print_time INTEGER, -- in minutes
    material_notes TEXT,
    customer_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    planned_date DATE,
    completed_date DATE,
    metadata JSON -- flexible field for platform-specific data
);

-- Trending cache table
CREATE TABLE trending_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    model_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    thumbnail_local_path TEXT,
    downloads INTEGER,
    likes INTEGER,
    creator TEXT,
    category TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(platform, model_id)
);

-- Tags table for many-to-many relationship
CREATE TABLE idea_tags (
    idea_id INTEGER,
    tag TEXT,
    FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE,
    PRIMARY KEY (idea_id, tag)
);
```

### API Endpoints

#### Ideas Management
```
GET    /api/ideas                 - List all ideas with filtering
POST   /api/ideas                 - Create new idea
GET    /api/ideas/{id}           - Get specific idea
PUT    /api/ideas/{id}           - Update idea
DELETE /api/ideas/{id}           - Delete idea
PATCH  /api/ideas/{id}/status    - Update idea status
```

#### External Integration
```
POST   /api/ideas/import          - Import from URL
GET    /api/ideas/parse-url       - Parse and preview URL metadata
POST   /api/ideas/{id}/download   - Trigger model download
```

#### Trending
```
GET    /api/trending/{platform}   - Get trending models
POST   /api/trending/refresh      - Force refresh trending cache
POST   /api/trending/{id}/save    - Save trending item as idea
```

#### Filters and Search
```
GET    /api/ideas/tags            - Get all available tags
GET    /api/ideas/stats           - Statistics (counts by status, category)
GET    /api/ideas/search          - Full-text search
```

### Frontend Components

#### Main View Structure
```
Ideas Section
├── Navigation Tabs
│   ├── My Ideas (personal ideas)
│   ├── Bookmarks (saved from platforms)
│   └── Trending (discovery feed)
├── Filter Bar
│   ├── Type Filter (All/Business/Personal)
│   ├── Status Filter
│   ├── Category Filter
│   └── Sort Options (Priority/Date/Status)
├── Content Grid
│   └── Idea Cards (responsive grid layout)
└── Action Bar
    ├── Add New Idea
    ├── Import from URL
    └── Refresh Trending
```

#### Idea Card Component
```
┌─────────────────────┐
│   [Thumbnail]       │
├─────────────────────┤
│ Title               │
│ Category · Priority │
│ ⏱ 2.5h · 🏢 Business│
├─────────────────────┤
│ [Plan] [Download]   │
└─────────────────────┘
```

#### Idea Detail Modal
- Full-screen modal with tabs
- Edit mode with inline fields
- Action buttons for workflow progression
- History log of status changes
- Related ideas suggestions

## Implementation Plan

### Development Phases

#### Phase 1.1 - Database and Backend (Week 1)
- [ ] Create database migrations
- [ ] Implement ideas CRUD API
- [ ] Add validation and business logic
- [ ] Create test data fixtures

#### Phase 1.2 - Basic Frontend (Week 2)
- [ ] Ideas list view with grid layout
- [ ] Add/Edit idea modal
- [ ] Basic filtering and sorting
- [ ] Status workflow implementation

#### Phase 1.3 - External Integration (Week 3)
- [ ] URL parser for Makerworld/Printables
- [ ] Metadata extraction service
- [ ] Thumbnail caching system
- [ ] Import workflow UI

#### Phase 1.4 - Trending Feature (Week 4)
- [ ] Platform API research and integration
- [ ] Background job scheduler
- [ ] Trending view component
- [ ] Cache management

#### Phase 1.5 - Polish and Testing (Week 5)
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Integration testing
- [ ] Documentation

### Technology Stack

#### Backend
- **Framework**: FastAPI (async support for background jobs)
- **Database**: SQLite with SQLAlchemy ORM
- **Background Jobs**: APScheduler or Celery
- **Web Scraping**: BeautifulSoup4 + requests (fallback for APIs)
- **Image Processing**: Pillow for thumbnail generation

#### Frontend
- **Framework**: React or Vue.js
- **UI Components**: Tailwind CSS or Material-UI
- **State Management**: Redux/Vuex or Context API
- **HTTP Client**: Axios
- **Image Loading**: Lazy loading with intersection observer

#### External Services
- **Makerworld API**: Research required (may need web scraping)
- **Printables API**: REST API available
- **Image CDN**: Consider Cloudinary for thumbnail optimization

## Testing Strategy

### Unit Tests
- Model validation
- API endpoint responses
- URL parsing accuracy
- Cache expiration logic

### Integration Tests
- Database operations
- External API interactions
- File system operations (thumbnails)
- Background job execution

### E2E Tests
- Complete idea workflow
- Import from external platforms
- Trending updates
- Search and filtering

## Performance Considerations

### Optimizations
- Lazy loading for idea grid
- Thumbnail optimization (WebP format)
- Database indexing on frequently queried fields
- API response pagination
- Frontend virtualization for large lists

### Caching Strategy
- Trending data: 6-hour TTL
- Thumbnails: Permanent until manual cleanup
- API responses: 5-minute cache for list views
- User preferences: Local storage

## Security Considerations

- Input sanitization for all user inputs
- URL validation before parsing
- Rate limiting for external API calls
- Secure file storage for thumbnails
- XSS prevention in rendered content

## Success Metrics

### Key Performance Indicators
- Ideas created per user per month
- Conversion rate (idea → printed)
- Average time from idea to print
- Trending item engagement rate
- External bookmark usage

### User Experience Metrics
- Page load time < 2 seconds
- Search response < 500ms
- Thumbnail load time < 1 second
- Zero data loss incidents

## Migration and Rollback Plan

### Data Migration
- No existing data to migrate for new feature
- Future: Export/import functionality for ideas

### Feature Flags
- Gradual rollout with feature toggles
- A/B testing for UI variations
- Quick disable mechanism if issues arise

## Documentation Requirements

### User Documentation
- Feature overview and benefits
- Step-by-step guides for common tasks
- FAQ section
- Video tutorials for complex workflows

### Developer Documentation
- API reference with examples
- Database schema documentation
- Integration guide for external platforms
- Contribution guidelines

## Open Questions and Decisions

### Platform API Access
1. **Makerworld API**: Currently investigating official API availability
   - Fallback: Web scraping with respectful rate limiting
   - Alternative: Manual URL paste only

2. **Printables API**: Documented REST API available
   - Need to register for API key
   - Rate limits to be determined

### Business Logic Decisions
1. Should ideas automatically transition to "planned" when added to queue?
2. How long should completed ideas remain visible before archiving?
3. Should we enforce unique titles for ideas?
4. What happens to ideas when associated models are removed from platforms?

### UI/UX Decisions
1. Grid vs. list view as default?
2. Number of items per page?
3. Mobile-first or desktop-first design?
4. Dark mode support priority?

## Maintenance and Support

### Regular Tasks
- Weekly trending cache analysis
- Monthly thumbnail storage cleanup
- Quarterly external API compatibility check
- Performance monitoring and optimization

### Support Channels
- In-app feedback mechanism
- GitHub issues for bug reports
- Feature request voting system
- Community forum for idea sharing

## Conclusion

The Ideas Section represents a significant enhancement to Printernizer, transforming it from a print management tool to a comprehensive 3D printing workflow solution. By bridging the gap between inspiration and execution, this feature will provide users with a seamless experience from discovering models to completing prints, while maintaining the business tracking capabilities that set Printernizer apart.

## Next Steps

1. Finalize API research for external platforms
2. Set up development environment with test data
3. Begin Phase 1.1 implementation
4. Create initial UI mockups for review
5. Establish testing framework

---

*Document Version: 1.0.0*
*Last Updated: 2025-09-22*
*Status: Planning Phase*