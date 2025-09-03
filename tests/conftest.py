"""
Pytest configuration and shared fixtures for Printernizer tests
"""
import pytest
import sqlite3
import tempfile
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import asyncio
from contextlib import asynccontextmanager


# =====================================================
# DATABASE FIXTURES
# =====================================================

@pytest.fixture
def temp_database():
    """Create temporary SQLite database for testing"""
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    # Read schema file and create database
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database_schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    conn = sqlite3.connect(temp_db.name)
    conn.executescript(schema_sql)
    conn.close()
    
    yield temp_db.name
    
    # Cleanup
    os.unlink(temp_db.name)


@pytest.fixture
def db_connection(temp_database):
    """Database connection fixture"""
    conn = sqlite3.connect(temp_database)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sample_printer_data():
    """Sample printer data for testing"""
    return [
        {
            'id': 'bambu_a1_001',
            'name': 'Bambu Lab A1 #1',
            'type': 'bambu_lab',
            'model': 'A1',
            'ip_address': '192.168.1.100',
            'access_code': 'test_access_code',
            'serial_number': 'AC12345678',
            'is_active': True,
            'status': 'online',
            'has_camera': True,
            'has_ams': True,
            'supports_remote_control': True
        },
        {
            'id': 'prusa_core_001',
            'name': 'Prusa Core One #1',
            'type': 'prusa',
            'model': 'Core One',
            'ip_address': '192.168.1.101',
            'api_key': 'test_api_key_12345',
            'is_active': True,
            'status': 'offline',
            'has_camera': False,
            'has_ams': False,
            'supports_remote_control': True
        }
    ]


@pytest.fixture
def sample_job_data():
    """Sample job data for testing"""
    return [
        {
            'printer_id': 'bambu_a1_001',
            'job_name': 'test_cube.3mf',
            'status': 'printing',
            'progress': 45.7,
            'layer_current': 150,
            'layer_total': 328,
            'material_type': 'PLA',
            'material_brand': 'OVERTURE',
            'material_color': 'White',
            'material_estimated_usage': 25.5,
            'material_cost_per_gram': 0.05,
            'layer_height': 0.2,
            'infill_percentage': 20,
            'nozzle_temperature': 210,
            'bed_temperature': 60,
            'estimated_duration': 7200,
            'is_business': True,
            'customer_name': 'Test Customer GmbH'
        },
        {
            'printer_id': 'prusa_core_001',
            'job_name': 'prototype_v1.stl',
            'status': 'completed',
            'progress': 100.0,
            'layer_current': 200,
            'layer_total': 200,
            'material_type': 'PETG',
            'material_brand': 'OVERTURE',
            'material_color': 'Black',
            'actual_duration': 5400,
            'is_business': False,
            'quality_rating': 4,
            'first_layer_adhesion': 'good'
        }
    ]


@pytest.fixture
def sample_file_data():
    """Sample file data for testing"""
    return [
        {
            'id': 'file_001',
            'printer_id': 'bambu_a1_001',
            'filename': 'test_cube.3mf',
            'original_filename': 'Test Cube (Original).3mf',
            'file_type': '.3mf',
            'file_size': 1024000,
            'printer_path': '/storage/test_cube.3mf',
            'download_status': 'available',
            'estimated_print_time': 7200,
            'layer_count': 328,
            'layer_height': 0.2,
            'infill_percentage': 20,
            'material_type': 'PLA'
        },
        {
            'id': 'file_002', 
            'printer_id': 'prusa_core_001',
            'filename': 'prototype_v1.stl',
            'file_type': '.stl',
            'file_size': 2048000,
            'local_path': '/downloads/prusa/2025-09-03/prototype_v1.stl',
            'download_status': 'downloaded',
            'downloaded_at': '2025-09-03T14:30:00Z'
        }
    ]


@pytest.fixture
def populated_database(db_connection, sample_printer_data, sample_job_data, sample_file_data):
    """Database with sample data populated"""
    cursor = db_connection.cursor()
    
    # Insert printers
    for printer in sample_printer_data:
        columns = ', '.join(printer.keys())
        placeholders = ', '.join(['?' for _ in printer])
        cursor.execute(f"INSERT INTO printers ({columns}) VALUES ({placeholders})", 
                      list(printer.values()))
    
    # Insert jobs
    for job in sample_job_data:
        columns = ', '.join(job.keys())
        placeholders = ', '.join(['?' for _ in job])
        cursor.execute(f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", 
                      list(job.values()))
    
    # Insert files
    for file_data in sample_file_data:
        columns = ', '.join(file_data.keys())
        placeholders = ', '.join(['?' for _ in file_data])
        cursor.execute(f"INSERT INTO files ({columns}) VALUES ({placeholders})", 
                      list(file_data.values()))
    
    db_connection.commit()
    return db_connection


# =====================================================
# API MOCK FIXTURES
# =====================================================

@pytest.fixture
def mock_bambu_api():
    """Mock Bambu Lab API responses"""
    mock_api = Mock()
    
    # Mock printer status
    mock_api.get_status.return_value = {
        'print': {
            'gcode_state': 'RUNNING',
            'mc_percent': 45,
            'mc_remaining_time': 3600,
            'layer_num': 150,
            'total_layer_num': 328
        },
        'temperature': {
            'nozzle_temper': 210.5,
            'nozzle_target_temper': 210.0,
            'bed_temper': 60.2,
            'bed_target_temper': 60.0,
            'chamber_temper': 28.5
        },
        'system': {
            'sequence_id': '12345',
            'command': 'push_status',
            'msg_id': '1',
            'time_stamp': '1693747800'
        }
    }
    
    # Mock file listing
    mock_api.get_files.return_value = [
        {
            'name': 'test_cube.3mf',
            'path': '/storage/test_cube.3mf',
            'size': 1024000,
            'date': '2025-09-03T10:00:00Z'
        }
    ]
    
    return mock_api


@pytest.fixture
def mock_prusa_api():
    """Mock Prusa PrusaLink API responses"""
    mock_api = Mock()
    
    # Mock printer status
    mock_api.get_status.return_value = {
        'printer': {
            'state': 'Operational',
            'temperature': {
                'tool0': {'actual': 25.0, 'target': 0.0},
                'bed': {'actual': 25.0, 'target': 0.0}
            }
        },
        'job': {
            'state': 'Operational',
            'file': {'name': None},
            'progress': {'completion': None, 'printTime': None, 'printTimeLeft': None}
        }
    }
    
    # Mock file listing
    mock_api.get_files.return_value = {
        'files': [
            {
                'name': 'prototype_v1.stl',
                'path': 'prototype_v1.stl',
                'size': 2048000,
                'date': 1693747800
            }
        ]
    }
    
    return mock_api


# =====================================================
# WEBSOCKET TEST FIXTURES
# =====================================================

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing"""
    mock_ws = MagicMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


class AsyncMock(MagicMock):
    """Async mock for testing async functions"""
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


# =====================================================
# BUSINESS LOGIC FIXTURES
# =====================================================

@pytest.fixture
def german_business_config():
    """German business configuration for testing"""
    return {
        'timezone': 'Europe/Berlin',
        'currency': 'EUR',
        'vat_rate': 0.19,
        'power_rate_per_kwh': 0.30,
        'default_material_cost_per_gram': 0.05,
        'business_hours': {
            'start': '08:00',
            'end': '18:00',
            'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        }
    }


@pytest.fixture
def sample_cost_calculations():
    """Sample cost calculation data"""
    return {
        'material_usage_grams': 25.5,
        'material_cost_per_gram': 0.05,
        'print_duration_hours': 2.5,
        'power_consumption_kwh': 0.3,
        'power_rate_per_kwh': 0.30,
        'labor_hours': 0.5,
        'labor_rate_per_hour': 15.0,
        'vat_rate': 0.19
    }


# =====================================================
# FILE SYSTEM FIXTURES
# =====================================================

@pytest.fixture
def temp_download_directory():
    """Temporary directory for file download testing"""
    temp_dir = tempfile.mkdtemp(prefix='printernizer_test_')
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_3mf_file():
    """Sample 3MF file content for testing"""
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="Title">Test Cube</metadata>
  <metadata name="Designer">Printernizer Test Suite</metadata>
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0" />
          <vertex x="20" y="0" z="0" />
          <vertex x="20" y="20" z="0" />
          <vertex x="0" y="20" z="0" />
          <vertex x="0" y="0" z="20" />
          <vertex x="20" y="0" z="20" />
          <vertex x="20" y="20" z="20" />
          <vertex x="0" y="20" z="20" />
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2" />
          <triangle v1="0" v2="2" v3="3" />
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1" />
  </build>
</model>'''


# =====================================================
# TEST UTILITIES
# =====================================================

@pytest.fixture
def test_utils():
    """Collection of test utility functions"""
    class TestUtils:
        @staticmethod
        def berlin_timestamp(date_str=None):
            """Convert date string to Berlin timezone timestamp"""
            from datetime import datetime
            import pytz
            
            if date_str is None:
                date_str = "2025-09-03T14:30:00"
            
            dt = datetime.fromisoformat(date_str)
            berlin_tz = pytz.timezone('Europe/Berlin')
            return berlin_tz.localize(dt)
        
        @staticmethod
        def calculate_vat(amount, rate=0.19):
            """Calculate VAT for German business logic"""
            return round(amount * rate, 2)
        
        @staticmethod
        def format_currency(amount):
            """Format currency for German locale"""
            return f"{amount:.2f} EUR"
        
        @staticmethod
        def generate_test_file_id():
            """Generate unique test file ID"""
            import uuid
            return f"test_{uuid.uuid4().hex[:8]}"
    
    return TestUtils()


# =====================================================
# ASYNC TEST SUPPORT
# =====================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =====================================================
# HTTP CLIENT FIXTURES
# =====================================================

@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    import requests
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    return session


# =====================================================
# ERROR TESTING FIXTURES
# =====================================================

@pytest.fixture
def network_error_scenarios():
    """Network error scenarios for testing"""
    return {
        'connection_timeout': requests.exceptions.ConnectTimeout,
        'read_timeout': requests.exceptions.ReadTimeout,
        'connection_error': requests.exceptions.ConnectionError,
        'http_error_404': requests.exceptions.HTTPError,
        'http_error_500': requests.exceptions.HTTPError,
        'invalid_json': json.JSONDecodeError('Expecting value', '', 0)
    }


# =====================================================
# PERFORMANCE TEST FIXTURES
# =====================================================

@pytest.fixture
def performance_test_data():
    """Data for performance testing"""
    return {
        'large_job_count': 1000,
        'concurrent_requests': 50,
        'large_file_size_mb': 100,
        'stress_test_duration_seconds': 60
    }


# =====================================================
# CONFIGURATION FIXTURES
# =====================================================

@pytest.fixture
def test_config():
    """Test configuration settings"""
    return {
        'database_url': 'sqlite:///:memory:',
        'api_base_url': 'http://localhost:8000/api/v1',
        'websocket_url': 'ws://localhost:8000/ws',
        'test_timeout_seconds': 30,
        'max_retries': 3,
        'log_level': 'DEBUG'
    }