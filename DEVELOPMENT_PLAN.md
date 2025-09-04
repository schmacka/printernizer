# Printernizer Development Plan

## Project Overview
**Printernizer** is a professional 3D print management system for Bambu Lab A1 and Prusa Core One printers, designed specifically for Porcus3D's German 3D printing service with enterprise-grade features.

---

## Development Phases & Milestones

### Phase 1: Foundation & Core Infrastructure (Weeks 1-2)
**Goal**: Establish basic project structure, database, and printer connectivity

#### Milestone 1.1: Project Setup & Architecture
- [x] Create Python project structure with virtual environment
- [x] Set up SQLite database schema for job tracking
- [x] Configure logging system (English language) - structlog implemented
- [ ] Implement configuration management (printers, API keys) - **IN PROGRESS**
- [x] Create basic web framework structure (Flask/FastAPI) - FastAPI implemented

#### Milestone 1.2: Printer API Integration
- [ ] Implement Bambu Lab MQTT integration using bambulabs-api
  - [ ] Connection establishment with IP + Access Code + Serial
  - [ ] Real-time status monitoring
  - [ ] Temperature and job progress tracking
- [ ] Implement Prusa Core One HTTP API integration
  - [ ] PrusaLink API key authentication
  - [ ] Job status and file list retrieval
  - [ ] 30-second polling implementation

#### Milestone 1.3: Basic Job Monitoring
- [ ] Create Job model with SQLite schema
- [ ] Implement real-time job tracking for both printer types
- [ ] Basic job status updates and persistence
- [ ] Error handling and connection recovery

**Deliverable**: Working printer connections with basic job monitoring

---

### Phase 2: File Management System (Weeks 3-4)
**Goal**: Complete "Drucker-Dateien" management system with download capabilities

#### Milestone 2.1: File Discovery & Listing
- [ ] Automatic printer file detection for Bambu Lab
- [ ] Automatic printer file detection for Prusa Core One
- [ ] Combined file listing (local + printer files)
- [ ] File status tracking system (📁 Available, ✓ Downloaded, 💾 Local)

#### Milestone 2.2: Download System
- [ ] One-click download functionality from web GUI
- [ ] Smart download organization by printer/date
- [ ] Secure file naming conventions
- [ ] Download progress tracking and status updates
- [ ] Error handling for failed downloads

#### Milestone 2.3: File Management Features
- [ ] Filter options by printer and download status
- [ ] Download statistics and reporting
- [ ] Cleanup management for old downloads
- [ ] File integrity verification

**Deliverable**: Complete file management system with download capabilities

---

### Phase 3: Web Interface Development (Weeks 5-6)
**Goal**: Professional web interface for printer and file management

#### Milestone 3.1: Core Web Interface
- [ ] Responsive web design (mobile-first approach)
- [ ] Real-time dashboard showing printer status
- [ ] Job monitoring interface with live updates
- [ ] File management interface with download buttons

#### Milestone 3.2: User Experience Features
- [ ] Real-time updates using WebSockets/Server-Sent Events
- [ ] Intuitive navigation and user interface
- [ ] Status indicators and progress bars
- [ ] Error notifications and user feedback

#### Milestone 3.3: Advanced Interface Features
- [ ] File preview thumbnails (if available)
- [ ] Bulk operations for file management
- [ ] Search and filtering capabilities
- [ ] Settings and configuration panel

**Deliverable**: Complete web interface for all core features

---

### Phase 4: Business & Analytics Features (Weeks 7-8)
**Goal**: Business-focused features for Porcus3D operations

#### Milestone 4.1: Cost Calculation System
- [ ] Material cost tracking based on job data
- [ ] Power consumption calculations
- [ ] Time-based cost calculations
- [ ] Business vs. private job categorization

#### Milestone 4.2: Export & Reporting
- [ ] Excel export functionality for accounting software
- [ ] CSV export with German business requirements
- [ ] Material consumption reports
- [ ] Business statistics and analytics
- [ ] German timezone and locale support

#### Milestone 4.3: Advanced Business Features
- [ ] Profit margin calculations
- [ ] Customer job tracking
- [ ] Material inventory management
- [ ] Business performance metrics

**Deliverable**: Complete business analytics and export system

---

### Phase 5: 3D Preview System (Weeks 9-10)
**Goal**: Advanced 3D file preview capabilities

#### Milestone 5.1: Multi-Format Support
- [ ] STL file preview using Trimesh
- [ ] 3MF file preview capabilities
- [ ] G-Code visualization using matplotlib
- [ ] Automatic format detection

#### Milestone 5.2: Preview Interface
- [ ] Click-to-preview from print list
- [ ] Modal view for detailed examination
- [ ] Multiple rendering backends
- [ ] Zoom, rotate, and pan controls

#### Milestone 5.3: Performance Optimization
- [ ] Intelligent caching system
- [ ] Lazy loading for large files
- [ ] Thumbnail generation
- [ ] Performance monitoring

**Deliverable**: Complete 3D preview system

---

### Phase 6: Advanced Features & Polish (Weeks 11-12)
**Goal**: Additional features and system refinement

#### Milestone 6.1: Home Assistant Integration Preparation
- [ ] Container-ready architecture
- [ ] Home Assistant addon structure
- [ ] MQTT discovery for Home Assistant
- [ ] Configuration templates

#### Milestone 6.2: System Optimization
- [ ] Performance profiling and optimization
- [ ] Memory usage optimization
- [ ] Database query optimization
- [ ] Error handling improvements

#### Milestone 6.3: Documentation & Deployment
- [ ] User documentation
- [ ] API documentation
- [ ] Deployment scripts
- [ ] Docker containerization

**Deliverable**: Production-ready system with advanced features

---

## Technical Architecture

### Technology Stack
- **Backend**: Python with Flask/FastAPI
- **Database**: SQLite with job-based architecture
- **MQTT**: bambulabs-api library for Bambu Lab
- **HTTP Client**: requests library for Prusa API
- **3D Processing**: Trimesh, numpy-stl, matplotlib
- **Web Frontend**: HTML5, CSS3, JavaScript (modern vanilla JS or light framework)

### Database Schema (SQLite)
```sql
-- Jobs table for print job tracking
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id TEXT NOT NULL,
    printer_type TEXT NOT NULL,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    estimated_duration INTEGER,
    actual_duration INTEGER,
    material_used REAL,
    material_cost REAL,
    power_cost REAL,
    is_business BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files table for tracking downloaded files
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT,
    file_size INTEGER,
    download_status TEXT DEFAULT 'available',
    downloaded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Printers configuration table
CREATE TABLE printers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    ip_address TEXT,
    api_key TEXT,
    access_code TEXT,
    serial_number TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Project Structure
```
printernizer/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLite models
│   │   └── migrations.py       # Database schema management
│   ├── printers/
│   │   ├── __init__.py
│   │   ├── base.py            # Base printer class
│   │   ├── bambu_lab.py       # Bambu Lab MQTT integration
│   │   └── prusa.py           # Prusa HTTP API integration
│   ├── file_manager/
│   │   ├── __init__.py
│   │   ├── downloader.py      # File download system
│   │   └── organizer.py       # File organization logic
│   ├── web/
│   │   ├── __init__.py
│   │   ├── app.py             # Web framework setup
│   │   ├── routes/            # Web routes
│   │   ├── templates/         # HTML templates
│   │   └── static/            # CSS, JS, images
│   ├── business/
│   │   ├── __init__.py
│   │   ├── analytics.py       # Business analytics
│   │   └── exports.py         # Excel/CSV export
│   └── preview/
│       ├── __init__.py
│       ├── stl_preview.py     # STL file preview
│       ├── threemf_preview.py # 3MF file preview
│       └── gcode_preview.py   # G-Code visualization
├── tests/                     # Unit and integration tests
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker setup
└── README.md                  # Project documentation
```

## Current Status & Next Steps

### ✅ Completed Infrastructure
1. **Project Structure**: Complete FastAPI backend with modular architecture
2. **Docker Setup**: Production and development containerization ready
3. **Database Schema**: SQLite schema defined with migrations
4. **API Routes**: Health, printers, jobs, files, analytics, system, websocket routes
5. **Test Framework**: Comprehensive test suite structure
6. **Deployment**: Production-ready with monitoring (Prometheus, Grafana)

### 🔄 Currently Working On (Phase 1.1)
1. **Missing Services**: ConfigService, EventService, Database implementations
2. **Configuration Management**: Environment-based printer and API key management
3. **Service Dependencies**: Complete the dependency injection system

### 🎯 Next Steps (Immediate)
1. **Implement Missing Services**: Complete the backend service layer
2. **Database Initialization**: Set up SQLite with proper migrations
3. **Printer API Integration**: Begin Bambu Lab and Prusa connections
4. **Basic Job Monitoring**: Real-time job tracking implementation

### Risk Assessment
- **API Dependencies**: Ensure bambulabs-api library stability and documentation
- **Real-time Updates**: WebSocket implementation complexity for live status
- **File Format Support**: 3D preview system complexity with multiple formats
- **German Business Requirements**: Ensure compliance with local accounting standards

### Success Metrics
- **Reliability**: 99%+ uptime for printer monitoring
- **Performance**: Sub-second response times for web interface
- **Usability**: One-click operations for common tasks
- **Business Value**: Automated reporting reduces manual work by 80%

---

*Last Updated: September 3, 2025*
*Status: Phase 1 - Foundation Development In Progress*