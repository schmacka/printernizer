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

#### Phase 1.1 - Database and Backend (Week 1) ✅ COMPLETED
- [x] Create database migrations
- [x] Implement ideas CRUD API
- [x] Add validation and business logic
- [x] Create test data fixtures
- [x] Add comprehensive unit tests (27 tests passing)
- [x] Integrate with main application

#### Phase 1.2 - Basic Frontend (Week 2) ⚠️ PARTIALLY COMPLETE
- [ ] Ideas list view with grid layout (moved to Phase 1.4)
- [ ] Add/Edit idea modal (moved to Phase 1.4)
- [ ] Basic filtering and sorting (moved to Phase 1.4)
- [ ] Status workflow implementation (moved to Phase 1.4)
- [x] Backend API foundation established
- [x] Service integration completed

#### Phase 1.3 - External Integration (Week 3) ✅ COMPLETED
- [x] URL parser for Makerworld/Printables
- [x] Metadata extraction service
- [x] Thumbnail caching system
- [x] Trending discovery service with background refresh
- [x] Platform API research and integration
- [x] Background job scheduler
- [x] Cache management
- [x] REST API endpoints for trending functionality
- [ ] Import workflow UI (moved to Phase 1.4)

#### Phase 1.4 - Frontend Implementation (Week 4)
- [ ] React/Vue.js components for Ideas management
- [ ] Trending view component with grid layout
- [ ] Import workflow UI for external platforms
- [ ] Material management frontend interface

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

1. ✅ ~~Finalize API research for external platforms~~
2. ✅ ~~Set up development environment with test data~~
3. ✅ ~~Begin Phase 1.1 implementation~~
4. ✅ ~~Complete Phase 1.3 external integration~~
5. 🚀 **Begin Phase 1.4 frontend implementation**
6. Create initial UI mockups for review
7. Implement trending discovery interface

---

*Document Version: 1.4.0*
*Last Updated: 2025-09-23*
*Status: Phase 1.4 Complete - Frontend Foundation Ready*

## Current Status Summary

### ✅ **Production Ready**
- **Ideas Creation**: Fully functional with proper validation and error handling
- **API Backend**: Complete REST API with 15+ endpoints
- **External Integration**: Trending discovery and URL parsing services
- **Material Tracking**: Full inventory and cost management system
- **Cross-Origin Support**: Works seamlessly via localhost and IP address access

### 🚀 **Ready for Enhancement**
The Ideas feature is now functionally complete for basic use cases. Users can:
1. Create and manage print ideas with full metadata
2. Access the system from any network location
3. Handle both business and personal project classification

### 📊 **Current Limitations**
- UI is basic HTML forms (functional but not optimized)
- No trending discovery frontend interface yet
- Missing visual status workflow
- Limited search and filtering capabilities in UI

## Implementation Status

### ✅ Completed (Phase 1.1 - Backend Foundation)
- **Database Schema**: Complete tables for ideas, trending cache, and tags
- **Backend API**: Full CRUD operations with 15 REST endpoints
- **Business Logic**: Validation, status workflows, and search functionality
- **Testing**: 27 unit tests covering all major functionality
- **Integration**: Fully integrated with Printernizer main application

### ⚠️ Phase 1.2 - Reorganized (Backend Priority)
- **Original Plan**: Basic frontend implementation
- **Actual Implementation**: Focused on backend completion and external integration
- **Rationale**: Backend-first approach ensures solid foundation before UI development
- **Status**: Frontend components moved to Phase 1.4 for consolidated UI implementation

### ✅ Completed (Phase 1.3 - External Integration)
- **URL Parser Service**: Enhanced support for MakerWorld, Printables, Thingiverse, MyMiniFactory, Cults3D
- **Trending Discovery**: Background refresh service with automatic caching (6-hour intervals)
- **Thumbnail Management**: Optimized image processing with Pillow, automatic cleanup, and WebP support
- **REST API Endpoints**: Complete trending functionality with /api/trending/*
- **Database Integration**: Trending cache tables with proper indexing and expiration
- **Service Architecture**: Full dependency injection and lifecycle management

### ✅ Bonus: Material Tracking System (Phase 1.3+)
- **Material Inventory Management**: Complete CRUD operations for material spools
- **Cost Tracking**: Per-kg pricing, total value calculations, remaining value analytics
- **Consumption Recording**: Job-based material usage tracking with cost attribution
- **Business Analytics**: Low stock alerts, consumption reports, Excel/CSV export
- **Material Types**: Support for PLA, PETG, TPU, ABS, ASA variants (OVERTURE, Prusament, Bambu)
- **REST API**: Complete /api/materials/* endpoints for inventory management
- **German Compliance**: EUR pricing, VAT-ready reporting, business/personal classification

### ✅ Completed (Phase 1.4 - Frontend Foundation & Connectivity)
- **Frontend API Integration**: Dynamic base URL configuration supporting localhost and IP access
- **CORS Configuration**: Cross-origin request support for IP-based access (192.168.176.159:8000)
- **Form Validation**: Proper handling of empty fields and data type conversion
- **User Experience**: Required field indicators with visual feedback (red asterisk)
- **Error Handling**: Improved frontend error reporting and user feedback
- **Ideas Creation**: Fully functional idea creation with validation and submission
- **API Router Structure**: Clean URL organization with /api/v1 prefix structure

### 🚀 Next Steps (Phase 1.5 - UI Enhancement & Features)
- **Ideas Management Interface**: Complete CRUD interface for viewing, editing, and organizing ideas
- **Trending Discovery UI**: Grid layout with thumbnail previews and platform integration
- **Import Workflow**: External platform URL import with metadata extraction
- **Material Management Frontend**: Inventory and consumption tracking UI
- **Mobile Responsive Design**: Touch-friendly interface optimization
- **Status Workflow**: Visual status progression (Idea → Planned → Printing → Completed)
- **Search & Filtering**: Advanced filtering by status, category, priority, and tags
- **Business Analytics**: Dashboard views for business vs personal project tracking

## Recommended Next Steps

### 🎯 **Immediate Priorities (Next 1-2 weeks)**

#### 1. **Ideas List View Enhancement** (Priority: HIGH)
- Replace basic form view with proper ideas grid/list display
- Implement idea card components with thumbnail support
- Add quick action buttons (Edit, Delete, Change Status)
- Enable sorting by date, priority, status

**Estimated Effort**: 2-3 days
**Impact**: Major UX improvement for daily usage

#### 2. **Status Workflow Implementation** (Priority: HIGH)
- Visual status badges (Idea/Planned/Printing/Completed)
- Quick status change buttons
- Status history tracking
- Progress indicators for active prints

**Estimated Effort**: 1-2 days
**Impact**: Core workflow functionality

#### 3. **Search and Filtering UI** (Priority: MEDIUM)
- Status filter dropdown (working backend already exists)
- Category/tag filtering
- Business vs Personal toggle
- Real-time search as user types

**Estimated Effort**: 1-2 days
**Impact**: Essential for users with many ideas

### 🔄 **Short-term Goals (Next 2-4 weeks)**

#### 4. **Trending Discovery Interface** (Priority: MEDIUM)
- Grid view of trending models from MakerWorld/Printables
- Platform filtering tabs
- One-click save to personal ideas
- Thumbnail loading with lazy loading

**Estimated Effort**: 3-4 days
**Impact**: New discovery feature, high user engagement

#### 5. **URL Import Workflow** (Priority: MEDIUM)
- Import modal with URL paste field
- Real-time preview of parsed metadata
- Batch import support
- Error handling for invalid URLs

**Estimated Effort**: 2-3 days
**Impact**: Streamlines external model bookmarking

#### 6. **Material Management Frontend** (Priority: LOW-MEDIUM)
- Material inventory dashboard
- Add/edit material spools interface
- Consumption tracking views
- Low stock alerts

**Estimated Effort**: 4-5 days
**Impact**: Business users, inventory management

### 🚀 **Medium-term Enhancements (1-2 months)**

#### 7. **Mobile Responsive Design**
- Touch-friendly interface
- Mobile-optimized layouts
- Gesture support for actions

#### 8. **Advanced Analytics**
- Business reporting dashboard
- Cost tracking visualizations
- Print success rate analytics
- Export functionality (Excel/CSV)

#### 9. **Performance Optimizations**
- Virtual scrolling for large lists
- Image optimization and WebP support
- Caching strategies for faster loading

### 🔧 **Technical Debt & Maintenance**

#### 10. **Code Quality Improvements**
- Frontend test coverage
- Error boundary implementation
- Loading state management
- Performance monitoring

#### 11. **Documentation Updates**
- User guide for Ideas feature
- API documentation refresh
- Developer onboarding docs

### 💡 **Quick Wins (Can be done anytime)**

- **Dark mode support** (1 day)
- **Keyboard shortcuts** (1 day)
- **Bulk operations** (select multiple ideas) (2 days)
- **Idea templates** (save common idea structures) (2 days)
- **Tags autocomplete** (1 day)

### 🎨 **UI/UX Considerations**

1. **Design System**: Consider implementing a consistent design system
2. **Accessibility**: Ensure WCAG compliance for screen readers
3. **Internationalization**: Prepare for multi-language support
4. **User Onboarding**: Add tooltips and guided tours for new users

### ⚡ **Performance Targets**

- **Ideas list loading**: < 500ms
- **Image thumbnails**: < 1s per image
- **Search results**: < 200ms
- **Status updates**: < 100ms (optimistic UI)

---

**Recommendation**: Start with **Ideas List View Enhancement** and **Status Workflow Implementation** as these provide the highest immediate value for users and build upon the solid foundation that's already in place.