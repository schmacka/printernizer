# API Reference

Complete REST API documentation for Printernizer. All endpoints follow RESTful conventions and return JSON responses.

## Base URL

```
http://localhost:8000/api/v1
```

## Available API Endpoints

### Core APIs

- **[Printers API](printers.md)** - Printer management, status, and control
- **[Jobs API](jobs.md)** - Print job tracking and history
- **[Files API](files.md)** - File browsing, downloads, and management
- **[Analytics API](analytics.md)** - Business metrics and reporting
- **[WebSocket API](websocket.md)** - Real-time updates and events

### System APIs

- **[Health API](#health-endpoints)** - Health checks and version info
- **[Settings API](#settings-endpoints)** - Configuration management
- **[System API](#system-endpoints)** - System utilities and diagnostics

## Quick Start

### Authentication

Currently, Printernizer does not require authentication. Future releases will include role-based access control.

### Request Format

All POST/PUT requests should include:

```http
Content-Type: application/json
```

### Response Format

All responses follow this structure:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional message"
}
```

Error responses:

```json
{
  "status": "error",
  "error": "Error description",
  "details": { ... }
}
```

### Example Request

```bash
# Get all printers
curl http://localhost:8000/api/v1/printers

# Get specific printer
curl http://localhost:8000/api/v1/printers/abc123

# Download a file
curl -X POST http://localhost:8000/api/v1/files/download \\
  -H "Content-Type: application/json" \\
  -d '{"printer_id": "abc123", "file_path": "/models/test.3mf"}'
```

## Interactive API Documentation

Printernizer includes interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Health Endpoints

### GET /api/v1/health

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.7.0",
  "uptime": 3600,
  "database": "connected"
}
```

### GET /api/v1/update-check

Check for available updates.

**Response:**
```json
{
  "current_version": "2.7.0",
  "latest_version": "2.7.0",
  "update_available": false,
  "release_url": "https://github.com/schmacka/printernizer/releases/latest"
}
```

## Auto-Generated Documentation

The following API documentation pages are auto-generated from the FastAPI OpenAPI specification:

- [Printers API](printers.md)
- [Jobs API](jobs.md)
- [Files API](files.md)
- [Analytics API](analytics.md)
- [WebSocket API](websocket.md)

## Rate Limiting

Currently, there are no rate limits. This may change in future releases.

## Versioning

The API uses URL versioning (e.g., `/api/v1/`). Breaking changes will increment the version number.

## Need Help?

- Check the [User Guide](../user-guide/index.md) for usage examples
- Review the [Architecture](../architecture/index.md) for technical details
- Visit [GitHub Issues](https://github.com/schmacka/printernizer/issues) to report problems
