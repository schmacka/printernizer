# Architecture

This section provides a comprehensive overview of Printernizer's architecture, design decisions, and technical implementation.

## Available Documentation

- **[System Design](service_architecture.md)** - Overall system architecture and service design
- **[API Specification](api_specification.md)** - Complete API reference and specifications
- **[Data Models](data_models.md)** - Database schemas and data structures
- **[Event Contracts](EVENT_CONTRACTS.md)** - Event system contracts and interfaces
- **[Event Flows](EVENT_FLOWS.md)** - Event flow diagrams and workflows
- **[Algorithms](ALGORITHMS.md)** - Core algorithms and implementation details
- **[Repository Pattern](repository-pattern.md)** - Data access layer design

## Architecture Overview

Printernizer is built as a modern, asynchronous web application using:

- **Backend:** FastAPI with async SQLite for high-performance API services
- **Frontend:** Vanilla JavaScript with modern ES6+ features
- **Communication:** WebSocket for real-time updates, REST API for operations
- **Printer Integration:** MQTT for Bambu Lab, HTTP for Prusa
- **Database:** SQLite with aiosqlite for async operations
- **Deployment:** Docker, Home Assistant add-on, standalone Python

## Key Design Principles

1. **Async-First**: All I/O operations are asynchronous for optimal performance
2. **Service-Oriented**: Clean separation of concerns through service classes
3. **Event-Driven**: Real-time updates via WebSocket and event system
4. **API-First**: RESTful API design for maximum interoperability
5. **Extensible**: Plugin architecture for printer integrations

## System Components

### Core Services
- **PrinterService** - Printer management and status tracking
- **JobService** - Print job monitoring and history
- **FileService** - File operations and downloads
- **AnalyticsService** - Business metrics and reporting

### Printer Integrations
- **BambuLabPrinter** - MQTT-based integration
- **PrusaPrinter** - HTTP API integration
- **BasePrinter** - Abstract base class for printer implementations

## For Developers

If you're looking to:

- **Understand the codebase** → Start with [System Design](service_architecture.md)
- **Integrate new features** → Review [API Specification](api_specification.md)
- **Add printer support** → See [Repository Pattern](repository-pattern.md)
- **Work with events** → Read [Event Contracts](EVENT_CONTRACTS.md)
- **Contribute code** → Check [Development Guide](../development/contributing.md)
