Primary Use Case: Managing Bambu Lab A1 and Prusa Core One printers with automated job tracking, file downloads, and business reporting.
Project represents a complete professional 3D print management solution with enterprise-grade features while maintaining simplicity for individual users.

### Core Components
- **Printer APIs**: Bambu Lab MQTT integration, Prusa PrusaLink HTTP API
- **Job Monitoring**: Real-time job tracking with 30-second polling intervals
- **File Management**: Automatic file downloads and organization
- **Database**: SQLite with job-based architecture
- **Webserver**: Accessable via Website. Desktop GUI can be done later

## Core Features:

### Job Monitoring

### 📁 Drucker-Dateien Management System
- **Automatische Drucker-Erkennung** von gespeicherten Dateien auf Bambu Lab & Prusa
- **One-Click Download** von Drucker-Dateien direkt aus der GUI
- **Kombinierte Dateiliste** zeigt lokale und Drucker-Dateien in einer Ansicht
- **Smart Download-Organisation** nach Drucker/Datum mit sicherer Dateibenennung
- **Status-Tracking**: Verfügbar 📁, Heruntergeladen ✓, Lokal 💾
- **Filter-Optionen** nach Drucker und Download-Status
- **Download-Statistiken** und Cleanup-Management





### 📈 Export und Business Features
- **Excel/CSV Export** für Buchhaltungssoftware
- **Kostenkalkulationen** mit Material- und Stromkosten
- **Materialverbrauch-Tracking** basierend auf Job-Daten
- **Business-Statistiken** für Geschäftszwecke

## Feature Ideas:
- **homeassistant addon container**

### 🎨 3D Vorschau System
- **STL/3MF/G-Code Preview** mit automatischer Format-Erkennung
- **Click-to-Preview** direkt aus der Druckliste
- **Multiple Rendering-Backends**: Trimesh, numpy-stl, matplotlib
- **Modal-Ansicht** für Detailbetrachtung
- **Intelligentes Caching** für Performance


## Business Logic

### Porcus3D Specific Requirements
- **Language**: English (logging, GUI, reports)
- **Business Categories**: Distinguish between business orders and private models
- **Material Tracking**: 
- **Location**: Kornwestheim, Germany (timezone, business rules)
- **Export**: Excel/CSV exports for accounting


## API Integration

### Bambu Lab A1
- **Protocol**: MQTT over bambulabs-api library
- **Authentication**: IP + Access Code + Serial Number
- **Features**: Real-time status, job progress, temperature monitoring
- **Polling**: Event-driven via MQTT callbacks

### Prusa Core One
- **Protocol**: HTTP REST API via PrusaLink
- **Authentication**: API Key
- **Features**: Job status, file downloads, print history
- **Polling**: HTTP requests every 30 seconds