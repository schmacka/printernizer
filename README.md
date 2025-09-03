# Printernizer - Professional 3D Printer Management System

A comprehensive web-based solution for managing Bambu Lab A1 and Prusa Core One 3D printers, designed specifically for Porcus3D's German 3D printing service.

## 🎯 Overview

Printernizer is an enterprise-grade 3D printer fleet management system that provides:

- **Real-time printer monitoring** - Live status updates via WebSocket
- **Job tracking and management** - Complete print job lifecycle monitoring  
- **Unified file management** - Centralized file handling with one-click downloads
- **Business analytics** - Cost tracking and reporting for commercial operations
- **German localization** - Full German language support with EUR currency

## 🏗️ Architecture

### Frontend (Phase 1 - Complete)
- **Technology**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Design**: Mobile-first responsive design with German business theme
- **Real-time**: WebSocket integration for live updates
- **Components**: Modular component architecture with reusable UI elements

### Backend (Planned)
- **API**: RESTful API with comprehensive endpoints
- **Database**: SQLite for job tracking and file management  
- **Integrations**: Bambu Lab MQTT and Prusa PrusaLink APIs
- **WebSocket**: Real-time communication server

## 🎨 User Interface

### Dashboard View
- Printer status cards with real-time temperature and job progress
- Overview statistics (active jobs, file counts, success rates)
- Recent jobs preview with progress tracking

### Printer Management  
- Add/configure Bambu Lab A1 and Prusa Core One printers
- Real-time connection status and diagnostics
- Detailed printer statistics and maintenance tracking

### Job Monitoring
- Complete job lifecycle tracking with filtering
- Real-time progress updates with layer information
- Business job classification and cost tracking

### File Management (Drucker-Dateien)
- Unified listing of local and printer files
- One-click downloads with progress monitoring
- File status tracking (Available 📁, Downloaded ✓, Local 💾)
- Cleanup management with storage optimization

## 🚀 Features

### Real-time Updates
- WebSocket connection for live printer status
- Automatic job progress updates
- File download progress monitoring
- System health monitoring

### German Business Integration
- Full German language interface
- EUR currency formatting with German locale
- Europe/Berlin timezone handling
- Business-focused cost tracking

### Mobile-First Design
- Responsive layout optimized for mobile devices
- Touch-friendly interface elements
- Efficient data presentation for small screens

### Error Handling
- Comprehensive API error handling
- Network resilience with retry logic
- User-friendly German error messages
- Connection status indicators

## 📁 Project Structure

```
printernizer/
├── frontend/                 # Complete Phase 1 frontend
│   ├── index.html           # Main application HTML
│   ├── css/                 
│   │   ├── main.css         # Core styles and theme
│   │   ├── dashboard.css    # Dashboard-specific styles
│   │   └── components.css   # Reusable component styles
│   ├── js/
│   │   ├── config.js        # Application configuration
│   │   ├── api.js           # API client with error handling
│   │   ├── websocket.js     # WebSocket client implementation
│   │   ├── utils.js         # Utility functions and formatters
│   │   ├── components.js    # Reusable UI components
│   │   ├── dashboard.js     # Dashboard page logic
│   │   ├── printers.js      # Printer management logic
│   │   ├── jobs.js          # Job monitoring logic
│   │   ├── files.js         # File management logic
│   │   └── main.js          # Application initialization
│   └── assets/              # Static assets
├── CLAUDE.md                # Development guidance
├── project.md               # Project requirements
├── api_specification.md     # Complete API documentation
├── data_models.md          # Data model definitions
└── README.md               # This file
```

## 🛠️ Technology Stack

### Frontend (Implemented)
- **HTML5** - Semantic markup with accessibility features
- **CSS3** - Custom properties, Grid, Flexbox, responsive design
- **JavaScript ES6+** - Modern JavaScript with classes and modules
- **WebSocket API** - Real-time communication
- **Fetch API** - HTTP requests with proper error handling

### Key Libraries (Vanilla Implementation)
- No external dependencies - pure vanilla JavaScript
- Custom component system for reusability
- Built-in German localization
- Responsive CSS Grid and Flexbox layouts

## 📊 API Integration

The frontend is designed to work with a comprehensive RESTful API:

### Core Endpoints
- `GET /api/v1/printers` - List all printers with status
- `GET /api/v1/jobs` - List print jobs with filtering
- `GET /api/v1/files` - Unified file listing  
- `POST /api/v1/files/{id}/download` - Download files
- WebSocket: `ws://localhost:8000/ws` - Real-time updates

### Features
- Comprehensive error handling with German messages
- Request retry logic for network resilience  
- Response caching for improved performance
- Rate limiting awareness

## 🎯 Business Features

### Cost Tracking
- Material cost calculation based on usage
- Power consumption monitoring
- Business vs. private job classification
- EUR currency formatting with German locale

### File Management
- Automatic printer file detection
- One-click downloads with progress tracking
- Local file organization by printer/date
- Storage cleanup with space optimization

### Analytics & Reporting
- Printer utilization statistics
- Job success rate tracking
- Material consumption reports
- Export capabilities for accounting integration

## 🌐 German Localization

### Language Support
- Complete German interface (Drucker, Aufträge, Dateien)
- German date/time formatting (DD.MM.YYYY HH:mm)
- EUR currency with German number formatting (1.234,56 €)
- German error messages and notifications

### Business Context
- Europe/Berlin timezone handling
- German business hours configuration
- Local market terminology and conventions

## 📱 Responsive Design

### Mobile-First Approach
- Optimized for mobile devices (320px and up)
- Touch-friendly interface elements
- Efficient information density
- Progressive enhancement for larger screens

### Breakpoints
- Mobile: 320px - 640px
- Tablet: 640px - 1024px  
- Desktop: 1024px and up

## 🔧 Configuration

### Application Settings
```javascript
// API Configuration
API_BASE_URL: 'http://localhost:8000/api/v1'
WEBSOCKET_URL: 'ws://localhost:8000/ws'

// German Localization
LANGUAGE: 'de'
TIMEZONE: 'Europe/Berlin'
CURRENCY: 'EUR'

// Update Intervals
DASHBOARD_REFRESH_INTERVAL: 30000  // 30 seconds
JOB_REFRESH_INTERVAL: 5000         // 5 seconds
```

## 🚀 Getting Started

### Prerequisites
- Modern web browser with WebSocket support
- Backend API server (to be implemented)

### Development Setup
1. Clone the repository
2. Open `frontend/index.html` in a web browser
3. The frontend will attempt to connect to `localhost:8000`

### Production Deployment
- Serve static files via web server (Apache/Nginx)
- Configure API endpoint URLs
- Set up SSL/HTTPS for production use

## 🔮 Future Enhancements

### Phase 2 Features
- 3D file preview system with STL/3MF rendering
- Advanced printer control interface
- Home Assistant addon container
- Desktop GUI application alternative

### Advanced Features  
- Multi-user support with role-based access
- Advanced analytics dashboard
- Automated job scheduling
- Print queue management

## 🏢 Business Integration

### Porcus3D Alignment
- Designed for sustainable 3D printing business model
- Supports corn starch-based material tracking
- German market compliance (GDPR, business requirements)
- Integration with existing Porcus3D workflow

### Scalability
- Supports multiple printer management
- Business vs. private job classification
- Cost tracking for commercial operations
- Export capabilities for accounting software

## 📝 Documentation

- **API Specification**: Complete RESTful API documentation
- **Data Models**: Comprehensive data structure definitions  
- **Integration Patterns**: WebSocket and API integration guides
- **CLAUDE.md**: Development guidance and architectural decisions

## 🤝 Contributing

This project follows the specifications defined in the project documentation. All development should align with:

- German business requirements
- Mobile-first responsive design
- Professional 3D printing workflow
- Porcus3D brand integration

## 📄 License

Proprietary software for Porcus3D 3D printing service.

---

**Printernizer v1.0.0** - Professional 3D Printer Management for Porcus3D  
*Entwickelt für nachhaltige 3D-Druck-Dienstleistungen in Deutschland*