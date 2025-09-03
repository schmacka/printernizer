# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Printernizer** is a professional 3D print management system designed for managing Bambu Lab A1 and Prusa Core One printers. It provides automated job tracking, file downloads, and business reporting capabilities specifically tailored for Porcus3D's German 3D printing service.

**Primary Use Case**: Enterprise-grade 3D printer fleet management with automated job monitoring, file organization, and business analytics while maintaining simplicity for individual users.

**Language**: English (for logging, GUI, and reports)
**Target Market**: Kornwestheim, Germany (timezone and business rules)
**Business Focus**: Distinguish between business orders and private models

## Architecture Overview

### Core Components
- **Printer APIs**: 
  - Bambu Lab MQTT integration via bambulabs-api library
  - Prusa PrusaLink HTTP API integration
- **Job Monitoring**: Real-time tracking with 30-second polling intervals
- **File Management**: Automatic downloads and organization system
- **Database**: SQLite with job-based architecture
- **Web Interface**: Primary access method (desktop GUI planned for later)

### API Integration Specifications

#### Bambu Lab A1
- **Protocol**: MQTT over bambulabs-api library
- **Authentication**: IP + Access Code + Serial Number
- **Features**: Real-time status, job progress, temperature monitoring
- **Polling**: Event-driven via MQTT callbacks

#### Prusa Core One  
- **Protocol**: HTTP REST API via PrusaLink
- **Authentication**: API Key
- **Features**: Job status, file downloads, print history
- **Polling**: HTTP requests every 30 seconds

## Core Feature Requirements

### Job Monitoring System
- Real-time job tracking for multiple printers
- 30-second polling intervals for status updates
- Job-based database architecture using SQLite

### File Management (Drucker-Dateien System)
- **Automatic printer detection** of saved files on Bambu Lab & Prusa
- **One-click downloads** directly from GUI
- **Combined file listing** showing local and printer files in unified view
- **Smart download organization** by printer/date with secure file naming
- **Status tracking**: Available 📁, Downloaded ✓, Local 💾
- **Filter options** by printer and download status
- **Download statistics** and cleanup management

### Business & Export Features
- **Excel/CSV export** for accounting software integration
- **Cost calculations** including material and power costs
- **Material consumption tracking** based on job data
- **Business statistics** for commercial operations

### 3D Preview System (Planned)
- **Multi-format support**: STL/3MF/G-Code with automatic format detection
- **Click-to-preview** directly from print list
- **Multiple rendering backends**: Trimesh, numpy-stl, matplotlib
- **Modal view** for detailed examination
- **Intelligent caching** for performance optimization

## Development Guidelines

### Business Logic Requirements
- **Porcus3D Integration**: Built specifically for Porcus3D's workflow
- **Material Tracking**: Comprehensive material usage monitoring
- **Location Awareness**: German timezone and business rules
- **Export Compatibility**: Excel/CSV formats for German accounting software

### Technology Stack Expectations
- **Database**: SQLite for job storage and tracking
- **Web Framework**: To be determined (Flask/FastAPI recommended)
- **MQTT Client**: bambulabs-api library for Bambu Lab integration
- **HTTP Client**: Standard library or requests for Prusa API
- **3D Processing**: Trimesh, numpy-stl, matplotlib for preview features

### File Organization
- Downloads organized by printer and date
- Secure file naming conventions
- Local file management with status tracking
- Integration with existing Porcus3D file structure

## Future Enhancements
- **Home Assistant addon container** for smart home integration
- **Desktop GUI application** as alternative to web interface
- **Advanced 3D preview capabilities** with multiple rendering options

## Development Notes
- This project is in the specification phase - no code has been implemented yet
- All architecture decisions should align with the core requirements in project.md
- Focus on enterprise features while maintaining simplicity
- Consider German business practices and accounting requirements