# Essential Tests for Printernizer Milestone 1.2: Printer API Integration

This directory contains a **focused test suite** for Milestone 1.2 printer integration functionality, following the user's requirement for a "limited set of tests without over-testing."

## Test Philosophy

- **Core functionality focus** - Tests essential printer integration workflows
- **Real-time monitoring validation** - WebSocket and polling mechanisms
- **German business compliance** - VAT, currency, timezone, and language support
- **Driver integration testing** - Bambu Lab MQTT and Prusa HTTP APIs
- **Quality over quantity** - Comprehensive coverage of critical paths only

## Milestone 1.2 Test Suite

### Backend Tests (Python/pytest)

#### 1. **`test_essential_printer_api.py`** - Core API Endpoints
Tests the 8 essential API endpoints from Milestone 1.2:

**Printer Status & Monitoring:**
- `GET /api/v1/printers/{id}/status` - Real-time status with temperatures and progress
- `GET /api/v1/printers/{id}/status/history` - Status history for trend monitoring  
- `POST /api/v1/printers/{id}/monitoring/start` - Start 30-second polling
- `POST /api/v1/printers/{id}/monitoring/stop` - Stop real-time monitoring

**File Management (Drucker-Dateien):**
- `GET /api/v1/printers/{id}/files` - List files with download status (📁✓💾)
- `POST /api/v1/printers/{id}/files/{filename}/download` - One-click downloads

**Job Integration:**
- `GET /api/v1/printers/{id}/jobs/current` - Current job with real-time progress
- `POST /api/v1/printers/{id}/jobs/sync` - Job history synchronization

**Key Test Areas:**
- Real-time monitoring with 30-second polling intervals
- German business data integration (19% VAT, EUR currency)
- Connection recovery and error handling
- German filename support (umlauts: äöüÄÖÜß)

#### 2. **`test_essential_printer_drivers.py`** - Driver Integration
Tests core printer driver functionality:

**Bambu Lab MQTT Integration:**
- MQTT connection via bambulabs-api library
- Real-time status updates through MQTT callbacks
- File listing and download via MQTT communication
- Connection error recovery with retry logic

**Prusa HTTP Integration:**
- HTTP API communication via PrusaLink
- 30-second polling for status updates
- File download through HTTP requests
- Job history synchronization

**Unified Interface:**
- Consistent status format across both drivers
- German business data handling consistency
- Connection recovery behavior validation

### Frontend Tests (JavaScript/Jest)

#### 3. **`frontend/test_essential_printer_monitoring.js`** - Real-time UI
Tests critical frontend monitoring components:

**Real-time Dashboard:**
- Printer status cards with German UI ("Druckt", "Bett", "Düse")
- WebSocket integration for live updates
- Temperature and progress display
- German filename rendering

**Drucker-Dateien Interface:**
- File list with status icons (📁 Available, ✓ Downloaded, 💾 Local)
- One-click download functionality
- Progress tracking with WebSocket updates
- German character support (Süßwarenform, Löffel)

**Monitoring Controls:**
- Start/Stop monitoring with German labels ("Überwachung starten")
- Connection status display ("Aktiv (30s Intervall)")
- Error handling with German messages

**German Business Integration:**
- VAT calculation display (19% German rate)
- EUR currency formatting
- German timezone handling (Europe/Berlin)
- Business vs private customer classification

## Key Testing Requirements

### ✅ Covered (Essential Only)
- **API Endpoints**: All 8 core printer integration endpoints
- **Real-time Monitoring**: 30-second polling and WebSocket updates
- **Driver Integration**: Bambu MQTT and Prusa HTTP communication
- **File Management**: Drucker-Dateien system with download status
- **German Business**: VAT, currency, timezone, and filename support
- **Connection Recovery**: Error handling and retry mechanisms
- **Frontend Integration**: Live monitoring dashboard with German UI

### ❌ Intentionally NOT Covered (Avoiding Over-Testing)
- Extensive error scenario combinations
- Performance stress testing under load
- Hardware-specific printer behaviors
- Complex WebSocket edge cases
- Exhaustive UI interaction testing
- Detailed 3D file format validation

## Running the Tests

### Quick Test Execution
```bash
# Run all Milestone 1.2 tests
python tests/run_milestone_1_2_tests.py

# With verbose output
python tests/run_milestone_1_2_tests.py --verbose

# With coverage report
python tests/run_milestone_1_2_tests.py --coverage
```

### Manual Test Execution
```bash
# Backend API integration tests
pytest tests/test_essential_printer_api.py -v

# Printer driver integration tests  
pytest tests/test_essential_printer_drivers.py -v

# Frontend monitoring tests (if Jest available)
npx jest tests/frontend/test_essential_printer_monitoring.js --verbose
```

## Test Dependencies

### Backend Requirements
```bash
pip install pytest pytest-asyncio aiohttp structlog
```

### Frontend Requirements (Optional)
```bash
npm install -g jest jsdom
```

## German Business Validation

All tests validate Porcus3D's German market requirements:

- **Timezone**: Europe/Berlin for all timestamps
- **Currency**: EUR formatting with German locale
- **VAT**: 19% German business tax rate  
- **Business Types**: GmbH, AG, UG customer classification
- **File Names**: German umlauts (äöüÄÖÜß) support
- **UI Language**: German interface labels and messages

## Test Data Examples

### German Business Customer Data
```python
{
    "customer_name": "Müller GmbH",
    "customer_type": "business",
    "material_cost_eur": 25.50,
    "vat_rate": 0.19,
    "total_cost": 30.35,  # Including 19% VAT
    "location": "Kornwestheim"
}
```

### German Filenames with Umlauts
- `Kundenauftrag_Müller.3mf`
- `Prototyp_Süßwarenform.stl`
- `Löffel_personalisiert.gcode`
- `Geschenk_Weihnachten.3mf`

### Real-time Status Data
```python
{
    "status": "printing",
    "temperature_bed": 65.0,
    "temperature_nozzle": 220.0,
    "progress": 67.3,
    "current_job": {
        "filename": "Firmenschild_Porcus3D.3mf",
        "customer_type": "business",
        "material_cost_eur": 15.75
    }
}
```

## Success Criteria

✅ **All tests pass** = Milestone 1.2 core printer integration functionality is validated

The test suite confirms:

1. **API Endpoints** respond correctly with German business data
2. **Real-time Monitoring** works with 30-second polling
3. **Printer Drivers** communicate properly (MQTT & HTTP)
4. **File Management** handles German filenames and downloads
5. **Frontend Integration** displays live updates with German UI
6. **Connection Recovery** handles errors gracefully
7. **German Business Logic** calculates VAT and formats currency correctly

## Test Output Example

```
🖨️ Printernizer Essential Tests - Milestone 1.2: Printer API Integration
================================================================================

📋 Testing core printer integration functionality:
   • Real-time printer monitoring (30-second polling)
   • Bambu Lab MQTT integration via bambulabs-api
   • Prusa Core One HTTP API integration
   • Drucker-Dateien file management system
   • German business logic and VAT calculations
   • WebSocket real-time updates

🔍 Checking test dependencies...
✅ All test dependencies are installed

🐍 Running Backend Tests (Python/pytest)
--------------------------------------------------
📋 Running tests: test_essential_printer_api.py, test_essential_printer_drivers.py
🚀 Command: pytest -v tests/test_essential_printer_api.py tests/test_essential_printer_drivers.py

tests/test_essential_printer_api.py::TestEssentialPrinterAPIEndpoints::test_printer_status_endpoint_real_time ✓
tests/test_essential_printer_api.py::TestEssentialPrinterAPIEndpoints::test_printer_monitoring_start_stop ✓
tests/test_essential_printer_api.py::TestEssentialPrinterAPIEndpoints::test_drucker_dateien_file_listing ✓
tests/test_essential_printer_api.py::TestEssentialPrinterAPIEndpoints::test_one_click_file_download ✓
tests/test_essential_printer_api.py::TestEssentialPrinterAPIEndpoints::test_current_job_real_time_progress ✓
tests/test_essential_printer_api.py::TestEssentialPrinterAPIEndpoints::test_job_sync_history_integration ✓

tests/test_essential_printer_drivers.py::TestEssentialBambuLabDriverIntegration::test_bambu_mqtt_connection_initialization ✓
tests/test_essential_printer_drivers.py::TestEssentialBambuLabDriverIntegration::test_bambu_real_time_status_via_mqtt ✓
tests/test_essential_printer_drivers.py::TestEssentialPrusaDriverIntegration::test_prusa_http_api_connection ✓
tests/test_essential_printer_drivers.py::TestEssentialPrusaDriverIntegration::test_prusa_30_second_polling_status ✓

🌐 Frontend Tests (JavaScript/Jest)
--------------------------------------------------
📋 Running: test_essential_printer_monitoring.js
🚀 Command: npx jest tests/frontend/test_essential_printer_monitoring.js --verbose

 PASS  tests/frontend/test_essential_printer_monitoring.js
  Essential Printer Monitoring Tests - Milestone 1.2
    Real-time Printer Status Dashboard
      ✓ should display printer status with German UI
      ✓ should handle WebSocket real-time updates
    Drucker-Dateien File Management
      ✓ should display file list with download status icons
      ✓ should handle one-click file download with progress

================================================================================
✅ All Milestone 1.2 Essential Tests Passed!

🎯 Core printer integration functionality validated:
   • Real-time printer status monitoring
   • Bambu Lab MQTT and Prusa HTTP drivers
   • File management (Drucker-Dateien system)
   • German business logic integration
   • WebSocket real-time updates
   • Connection recovery and error handling

🚀 Milestone 1.2: Printer API Integration - VALIDATED

⏱️  Test execution time: 3.47 seconds
📅 Completed: 2024-09-05 16:45:23
```

This focused test suite validates all critical printer integration functionality for Milestone 1.2 while adhering to the requirement for essential-only testing without over-engineering.