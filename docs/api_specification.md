# Printernizer API Specification v1.0

## Overview

RESTful API for Printernizer Phase 1 - Professional 3D print management system for Bambu Lab A1 and Prusa Core One printers. This API provides enterprise-grade printer monitoring, job tracking, and file management capabilities.

**Base URL**: `http://localhost:8000/api/v1`
**Content-Type**: `application/json`
**Authentication**: None (Phase 1 - local network deployment)

---

## API Endpoints

### 1. System Health & Status

#### GET /health
System health check and API status

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-03T14:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "active_printers": 2,
  "uptime_seconds": 86400
}
```

#### GET /system/info
System information and configuration summary

**Response 200:**
```json
{
  "system": {
    "version": "1.0.0",
    "timezone": "Europe/Berlin",
    "language": "en",
    "business_mode": true
  },
  "database": {
    "type": "sqlite",
    "jobs_count": 156,
    "files_count": 89,
    "printers_count": 2
  },
  "features": {
    "job_monitoring": true,
    "file_management": true,
    "business_analytics": false,
    "preview_system": false
  }
}
```

---

### 2. Printer Management

#### GET /printers
List all configured printers with current status

**Query Parameters:**
- `active` (boolean): Filter by active status
- `type` (string): Filter by printer type (bambu_lab, prusa)

**Response 200:**
```json
{
  "printers": [
    {
      "id": "bambu_a1_001",
      "name": "Bambu Lab A1 #1",
      "type": "bambu_lab",
      "model": "A1",
      "ip_address": "192.168.1.100",
      "serial_number": "AC12345678",
      "status": "online",
      "current_job": {
        "id": 123,
        "name": "test_print.3mf",
        "status": "printing",
        "progress": 45.7,
        "estimated_remaining": 3600
      },
      "temperatures": {
        "nozzle": 210.5,
        "bed": 60.0,
        "chamber": 28.5
      },
      "is_active": true,
      "last_seen": "2025-09-03T14:30:00Z",
      "created_at": "2025-09-01T10:00:00Z"
    },
    {
      "id": "prusa_core_001",
      "name": "Prusa Core One #1",
      "type": "prusa",
      "model": "Core One",
      "ip_address": "192.168.1.101",
      "status": "idle",
      "current_job": null,
      "temperatures": {
        "nozzle": 25.0,
        "bed": 25.0
      },
      "is_active": true,
      "last_seen": "2025-09-03T14:29:45Z",
      "created_at": "2025-09-01T10:00:00Z"
    }
  ],
  "total_count": 2,
  "active_count": 2
}
```

#### GET /printers/{printer_id}
Get detailed information for specific printer

**Response 200:**
```json
{
  "id": "bambu_a1_001",
  "name": "Bambu Lab A1 #1",
  "type": "bambu_lab",
  "model": "A1",
  "ip_address": "192.168.1.100",
  "serial_number": "AC12345678",
  "access_code": "12345678",
  "status": "online",
  "connection_status": "connected",
  "firmware_version": "1.04.00.00",
  "current_job": {
    "id": 123,
    "name": "test_print.3mf",
    "status": "printing",
    "progress": 45.7,
    "layer_current": 125,
    "layer_total": 274,
    "estimated_remaining": 3600,
    "started_at": "2025-09-03T12:00:00Z"
  },
  "temperatures": {
    "nozzle": 210.5,
    "nozzle_target": 210.0,
    "bed": 60.0,
    "bed_target": 60.0,
    "chamber": 28.5
  },
  "statistics": {
    "total_jobs": 45,
    "successful_jobs": 42,
    "failed_jobs": 3,
    "total_print_time": 345600,
    "material_used_total": 2.45
  },
  "capabilities": {
    "has_camera": true,
    "has_ams": true,
    "supports_remote_control": true
  },
  "is_active": true,
  "last_seen": "2025-09-03T14:30:00Z",
  "created_at": "2025-09-01T10:00:00Z"
}
```

#### POST /printers
Add new printer configuration

**Request Body:**
```json
{
  "id": "bambu_a1_002",
  "name": "Bambu Lab A1 #2",
  "type": "bambu_lab",
  "ip_address": "192.168.1.102",
  "access_code": "87654321",
  "serial_number": "AC87654321",
  "is_active": true
}
```

**Response 201:**
```json
{
  "id": "bambu_a1_002",
  "name": "Bambu Lab A1 #2",
  "type": "bambu_lab",
  "status": "configuring",
  "connection_status": "testing",
  "message": "Printer configuration created, testing connection...",
  "created_at": "2025-09-03T14:30:00Z"
}
```

#### PUT /printers/{printer_id}
Update printer configuration

**Request Body:**
```json
{
  "name": "Updated Printer Name",
  "ip_address": "192.168.1.103",
  "is_active": false
}
```

**Response 200:**
```json
{
  "id": "bambu_a1_001",
  "message": "Printer configuration updated successfully",
  "updated_at": "2025-09-03T14:30:00Z"
}
```

#### DELETE /printers/{printer_id}
Remove printer configuration

**Response 200:**
```json
{
  "message": "Printer configuration removed successfully",
  "deleted_at": "2025-09-03T14:30:00Z"
}
```

---

### 3. Job Monitoring

#### GET /jobs
List print jobs with filtering and pagination

**Query Parameters:**
- `printer_id` (string): Filter by printer
- `status` (string): Filter by job status (queued, printing, completed, failed, cancelled)
- `is_business` (boolean): Filter business vs private jobs
- `start_date` (ISO date): Filter jobs after date
- `end_date` (ISO date): Filter jobs before date
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 50, max: 100)
- `order_by` (string): Sort field (created_at, start_time, duration)
- `order_dir` (string): Sort direction (asc, desc)

**Response 200:**
```json
{
  "jobs": [
    {
      "id": 123,
      "printer_id": "bambu_a1_001",
      "printer_name": "Bambu Lab A1 #1",
      "job_name": "custom_bracket.3mf",
      "status": "printing",
      "progress": 45.7,
      "layer_current": 125,
      "layer_total": 274,
      "start_time": "2025-09-03T12:00:00Z",
      "estimated_duration": 7200,
      "estimated_completion": "2025-09-03T14:00:00Z",
      "actual_duration": 3300,
      "material_info": {
        "type": "PLA",
        "color": "Black",
        "estimated_usage": 45.5,
        "actual_usage": null
      },
      "file_info": {
        "size": 2048576,
        "path": "/prints/2025-09-03/custom_bracket.3mf"
      },
      "costs": {
        "material_cost": 2.28,
        "power_cost": 0.15,
        "total_cost": 2.43
      },
      "is_business": true,
      "created_at": "2025-09-03T11:55:00Z",
      "updated_at": "2025-09-03T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_items": 156,
    "total_pages": 4,
    "has_next": true,
    "has_previous": false
  },
  "summary": {
    "active_jobs": 2,
    "queued_jobs": 1,
    "completed_today": 5,
    "failed_today": 0
  }
}
```

#### GET /jobs/{job_id}
Get detailed information for specific job

**Response 200:**
```json
{
  "id": 123,
  "printer_id": "bambu_a1_001",
  "printer_name": "Bambu Lab A1 #1",
  "job_name": "custom_bracket.3mf",
  "status": "printing",
  "progress": 45.7,
  "layer_current": 125,
  "layer_total": 274,
  "start_time": "2025-09-03T12:00:00Z",
  "end_time": null,
  "estimated_duration": 7200,
  "actual_duration": 3300,
  "estimated_completion": "2025-09-03T14:00:00Z",
  "material_info": {
    "type": "PLA",
    "brand": "OVERTURE",
    "color": "Black",
    "estimated_usage": 45.5,
    "actual_usage": null,
    "cost_per_gram": 0.05
  },
  "file_info": {
    "filename": "custom_bracket.3mf",
    "size": 2048576,
    "path": "/prints/2025-09-03/custom_bracket.3mf",
    "hash": "sha256:abc123...",
    "uploaded_at": "2025-09-03T11:50:00Z"
  },
  "print_settings": {
    "layer_height": 0.2,
    "infill": 20,
    "print_speed": 100,
    "nozzle_temp": 210,
    "bed_temp": 60
  },
  "costs": {
    "material_cost": 2.28,
    "power_cost": 0.15,
    "labor_cost": 0.00,
    "total_cost": 2.43
  },
  "quality_metrics": {
    "first_layer_adhesion": "good",
    "surface_finish": "excellent",
    "dimensional_accuracy": 0.1
  },
  "is_business": true,
  "customer_info": {
    "order_id": "PO-2025-0234",
    "customer_name": "Max Mustermann GmbH"
  },
  "created_at": "2025-09-03T11:55:00Z",
  "updated_at": "2025-09-03T14:30:00Z"
}
```

#### POST /jobs/{job_id}/cancel
Cancel active print job

**Response 200:**
```json
{
  "id": 123,
  "status": "cancelled",
  "message": "Job cancellation initiated",
  "cancelled_at": "2025-09-03T14:30:00Z"
}
```

#### PUT /jobs/{job_id}
Update job information (business category, costs, etc.)

**Request Body:**
```json
{
  "is_business": true,
  "customer_info": {
    "order_id": "PO-2025-0234",
    "customer_name": "Max Mustermann GmbH"
  },
  "material_cost": 2.50,
  "notes": "High priority order"
}
```

**Response 200:**
```json
{
  "id": 123,
  "message": "Job information updated successfully",
  "updated_at": "2025-09-03T14:30:00Z"
}
```

---

### 4. File Management (Drucker-Dateien)

#### GET /files
List all files (local and printer files) with unified status tracking

**Query Parameters:**
- `printer_id` (string): Filter by printer
- `status` (string): Filter by download status (available, downloaded, local, error)
- `file_type` (string): Filter by file extension (.3mf, .stl, .gcode)
- `search` (string): Search in filename
- `page` (integer): Page number
- `limit` (integer): Items per page

**Response 200:**
```json
{
  "files": [
    {
      "id": "f123",
      "printer_id": "bambu_a1_001",
      "printer_name": "Bambu Lab A1 #1",
      "filename": "test_print.3mf",
      "file_size": 2048576,
      "file_type": ".3mf",
      "status": "available",
      "status_icon": "📁",
      "printer_path": "/cache/test_print.3mf",
      "local_path": null,
      "created_on_printer": "2025-09-03T10:00:00Z",
      "downloaded_at": null,
      "last_accessed": "2025-09-03T10:00:00Z",
      "download_url": "/api/v1/files/f123/download",
      "metadata": {
        "estimated_print_time": 7200,
        "layer_height": 0.2,
        "infill": 20
      }
    },
    {
      "id": "f124", 
      "printer_id": "bambu_a1_001",
      "printer_name": "Bambu Lab A1 #1",
      "filename": "bracket_v2.3mf",
      "file_size": 1536000,
      "file_type": ".3mf",
      "status": "downloaded",
      "status_icon": "✓",
      "printer_path": "/cache/bracket_v2.3mf",
      "local_path": "/downloads/bambu_a1_001/2025-09-03/bracket_v2.3mf",
      "created_on_printer": "2025-09-02T15:30:00Z",
      "downloaded_at": "2025-09-03T09:15:00Z",
      "last_accessed": "2025-09-03T09:15:00Z",
      "download_url": null,
      "checksum": "md5:def456..."
    },
    {
      "id": "f125",
      "printer_id": null,
      "printer_name": null,
      "filename": "local_design.stl",
      "file_size": 512000,
      "file_type": ".stl",
      "status": "local",
      "status_icon": "💾",
      "printer_path": null,
      "local_path": "/uploads/local_design.stl",
      "created_on_printer": null,
      "downloaded_at": null,
      "last_accessed": "2025-09-01T16:20:00Z",
      "upload_url": "/api/v1/files/f125/upload"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_items": 89,
    "total_pages": 2
  },
  "summary": {
    "available_count": 15,
    "downloaded_count": 62,
    "local_count": 12,
    "total_size": 134217728,
    "download_success_rate": 0.98
  }
}
```

#### GET /files/{file_id}
Get detailed information for specific file

**Response 200:**
```json
{
  "id": "f123",
  "printer_id": "bambu_a1_001",
  "printer_name": "Bambu Lab A1 #1",
  "filename": "test_print.3mf",
  "original_filename": "Custom Bracket Design.3mf",
  "file_size": 2048576,
  "file_type": ".3mf",
  "status": "available",
  "status_icon": "📁",
  "printer_path": "/cache/test_print.3mf",
  "local_path": null,
  "created_on_printer": "2025-09-03T10:00:00Z",
  "downloaded_at": null,
  "last_accessed": "2025-09-03T10:00:00Z",
  "download_attempts": 0,
  "download_url": "/api/v1/files/f123/download",
  "preview_url": "/api/v1/files/f123/preview",
  "metadata": {
    "estimated_print_time": 7200,
    "layer_height": 0.2,
    "layer_count": 274,
    "infill": 20,
    "support_material": false,
    "material_type": "PLA",
    "nozzle_temperature": 210,
    "bed_temperature": 60
  },
  "related_jobs": [
    {
      "id": 122,
      "status": "completed",
      "completed_at": "2025-09-02T16:30:00Z"
    }
  ]
}
```

#### POST /files/{file_id}/download
Initiate download of file from printer to local storage

**Response 202:**
```json
{
  "id": "f123",
  "status": "downloading",
  "message": "Download initiated",
  "download_id": "dl_456789",
  "estimated_duration": 30,
  "started_at": "2025-09-03T14:30:00Z"
}
```

#### GET /files/{file_id}/download/status
Check download progress

**Response 200:**
```json
{
  "download_id": "dl_456789",
  "file_id": "f123",
  "status": "downloading",
  "progress": 67.5,
  "bytes_downloaded": 1384448,
  "bytes_total": 2048576,
  "speed_mbps": 2.5,
  "estimated_remaining": 8,
  "started_at": "2025-09-03T14:30:00Z",
  "error": null
}
```

#### DELETE /files/{file_id}
Delete local file (does not affect printer)

**Response 200:**
```json
{
  "id": "f123",
  "message": "Local file deleted successfully",
  "status": "available",
  "deleted_at": "2025-09-03T14:30:00Z"
}
```

#### GET /files/cleanup/candidates
Get list of files that can be safely cleaned up

**Query Parameters:**
- `older_than_days` (integer): Files older than N days
- `min_size_mb` (integer): Minimum file size for cleanup
- `unused_only` (boolean): Only files not recently accessed

**Response 200:**
```json
{
  "cleanup_candidates": [
    {
      "id": "f100",
      "filename": "old_test.3mf",
      "file_size": 5242880,
      "downloaded_at": "2025-08-15T10:00:00Z",
      "last_accessed": "2025-08-15T10:00:00Z",
      "age_days": 19,
      "space_savings_mb": 5
    }
  ],
  "total_candidates": 12,
  "total_space_savings_mb": 156
}
```

#### POST /files/cleanup
Perform cleanup of selected files

**Request Body:**
```json
{
  "file_ids": ["f100", "f101", "f102"],
  "confirm": true
}
```

**Response 200:**
```json
{
  "cleaned_files": 3,
  "space_freed_mb": 45,
  "failed_cleanups": [],
  "completed_at": "2025-09-03T14:30:00Z"
}
```

---

### 5. Statistics & Analytics

#### GET /statistics/overview
Overall system statistics

**Query Parameters:**
- `period` (string): Time period (day, week, month, year)
- `start_date` (ISO date): Custom period start
- `end_date` (ISO date): Custom period end

**Response 200:**
```json
{
  "period": "month",
  "start_date": "2025-08-01T00:00:00Z",
  "end_date": "2025-08-31T23:59:59Z",
  "printers": {
    "total_active": 2,
    "online_count": 2,
    "utilization_rate": 0.67
  },
  "jobs": {
    "total_jobs": 89,
    "completed_jobs": 85,
    "failed_jobs": 4,
    "success_rate": 0.955,
    "total_print_time": 432000,
    "average_job_duration": 4847
  },
  "materials": {
    "total_used_kg": 12.5,
    "most_used_material": "OVERTURE PLA Black",
    "materials_breakdown": [
      {"material": "OVERTURE PLA Black", "used_kg": 4.2, "jobs": 35},
      {"material": "OVERTURE PLA White", "used_kg": 3.1, "jobs": 28},
      {"material": "OVERTURE PETG Clear", "used_kg": 2.8, "jobs": 15}
    ]
  },
  "business": {
    "business_jobs": 72,
    "private_jobs": 17,
    "business_percentage": 0.809,
    "revenue_estimate": 485.50
  },
  "files": {
    "total_files": 89,
    "downloaded_files": 62,
    "local_only_files": 12,
    "download_success_rate": 0.98,
    "total_storage_used_mb": 1024
  }
}
```

#### GET /statistics/printers/{printer_id}
Printer-specific statistics

**Response 200:**
```json
{
  "printer_id": "bambu_a1_001",
  "printer_name": "Bambu Lab A1 #1",
  "period": "month",
  "uptime": {
    "total_hours": 720,
    "active_hours": 485,
    "utilization_rate": 0.674
  },
  "jobs": {
    "total_jobs": 45,
    "completed_jobs": 42,
    "failed_jobs": 3,
    "cancelled_jobs": 0,
    "success_rate": 0.933,
    "average_duration": 4680
  },
  "materials": {
    "total_used_kg": 6.8,
    "cost_total": 340.00,
    "most_used": "OVERTURE PLA Black"
  },
  "maintenance": {
    "last_maintenance": "2025-08-15T10:00:00Z",
    "nozzle_changes": 1,
    "bed_calibrations": 12
  },
  "quality_metrics": {
    "first_layer_success_rate": 0.96,
    "average_surface_quality": 4.2,
    "dimensional_accuracy": 0.05
  }
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "PRINTER_OFFLINE",
    "message": "Printer bambu_a1_001 is currently offline",
    "details": {
      "printer_id": "bambu_a1_001",
      "last_seen": "2025-09-03T13:45:00Z",
      "connection_attempts": 3
    },
    "timestamp": "2025-09-03T14:30:00Z",
    "request_id": "req_123456"
  }
}
```

### HTTP Status Codes
- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **202 Accepted**: Request accepted for processing
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., printer already exists)
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error
- **502 Bad Gateway**: Printer communication error
- **503 Service Unavailable**: Service temporarily unavailable

### Common Error Codes
- `PRINTER_OFFLINE`: Printer not reachable
- `PRINTER_BUSY`: Printer currently busy with another job
- `FILE_NOT_FOUND`: Requested file doesn't exist
- `DOWNLOAD_FAILED`: File download failed
- `INVALID_PRINTER_CONFIG`: Printer configuration invalid
- `DATABASE_ERROR`: Database operation failed
- `VALIDATION_ERROR`: Request validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests

---

## WebSocket API (Real-time Updates)

### Connection Endpoint
`ws://localhost:8000/ws`

### Message Format
```json
{
  "type": "printer_status",
  "timestamp": "2025-09-03T14:30:00Z",
  "data": {
    "printer_id": "bambu_a1_001",
    "status": "printing",
    "progress": 46.2,
    "temperatures": {
      "nozzle": 210.8,
      "bed": 59.8
    }
  }
}
```

### Message Types
- `printer_status`: Real-time printer status updates
- `job_update`: Job progress and status changes
- `file_update`: File download progress
- `system_alert`: System notifications and alerts

---

## Rate Limiting

### Limits (per client IP)
- General API: 1000 requests/hour
- File downloads: 50 concurrent downloads
- WebSocket connections: 10 concurrent connections
- Status updates: 120 requests/minute (2 per second)

### Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1693747200
```

---

*API Specification Version 1.0 - Phase 1*
*Last Updated: September 3, 2025*