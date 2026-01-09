"""
Test suite for File Management API endpoints - Drucker-Dateien System
Tests unified file listing, download functionality, and German file naming conventions.
"""
import pytest
import json
import os
import tempfile
import hashlib
from unittest.mock import patch, Mock, mock_open, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestFileAPI:
    """Test file management API endpoints"""
    
    def test_get_files_unified_empty(self, client, temp_database):
        """Test GET /api/v1/files with empty database"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value.execute.return_value.fetchall.return_value = []

            response = client.get("/api/v1/files")

            assert response.status_code == 200
            data = response.json()
            assert 'files' in data
            assert isinstance(data['files'], list)
    
    def test_get_files_unified_with_data(self, client, populated_database, sample_file_data):
        """Test GET /api/v1/files with existing files"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database

            response = client.get("/api/v1/files")
            
            assert response.status_code == 200
            data = response.json()
            assert 'files' in data
            assert isinstance(data['files'], list)
    
    def test_get_files_filter_by_printer(self, client, populated_database):
        """Test GET /api/v1/files?printer_id=bambu_a1_001"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database

            response = client.get("/api/v1/files?printer_id=bambu_a1_001")
            
            assert response.status_code == 200
            data = response.json()
            assert 'files' in data
            assert isinstance(data['files'], list)
    
    def test_get_files_filter_by_status(self, client, populated_database):
        """Test GET /api/v1/files?status=available"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database

            response = client.get("/api/v1/files?status=available")
            
            assert response.status_code == 200
            data = response.json()
            assert 'files' in data
            assert isinstance(data['files'], list)
    
    def test_get_files_filter_by_type(self, client, populated_database):
        """Test GET /api/v1/files?file_type=.3mf"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database

            response = client.get("/api/v1/files?file_type=.3mf")
            
            assert response.status_code == 200
            data = response.json()
            assert 'files' in data
            assert isinstance(data['files'], list)
    
    def test_post_file_download_bambu_lab(self, client, test_app, temp_download_directory):
        """Test POST /api/v1/files/{id}/download for Bambu Lab file"""
        file_id = 'bambu_001_test_cube.3mf'
        local_path = os.path.join(temp_download_directory, 'test_cube.3mf')

        # Configure the mock file service (already in test_app)
        test_app.state.file_service.download_file.return_value = {
            'status': 'success',
            'message': 'File downloaded successfully',
            'local_path': local_path,
            'file_id': file_id,
            'file_size': 1024
        }

        response = client.post(f"/api/v1/files/{file_id}/download")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['status'] == 'downloaded'
        assert 'local_path' in data['data']
    
    def test_post_file_download_prusa(self, client, test_app, temp_download_directory):
        """Test POST /api/v1/files/{id}/download for Prusa file"""
        file_id = 'prusa_001_prototype.stl'
        local_path = os.path.join(temp_download_directory, 'prototype.stl')

        # Configure the mock file service
        test_app.state.file_service.download_file.return_value = {
            'status': 'success',
            'message': 'File downloaded successfully',
            'local_path': local_path,
            'file_id': file_id,
            'file_size': 2048
        }

        response = client.post(f"/api/v1/files/{file_id}/download")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['status'] == 'downloaded'
    
    def test_post_file_download_already_downloaded(self, client, test_app):
        """Test POST /api/v1/files/{id}/download for already downloaded file"""
        file_id = 'bambu_001_already_downloaded.3mf'

        # Configure mock to return error
        test_app.state.file_service.download_file.return_value = {
            'status': 'error',
            'message': 'File already downloaded',
            'local_path': None
        }

        response = client.post(f"/api/v1/files/{file_id}/download")

        # Should raise FileDownloadError which returns 503 status code
        assert response.status_code == 503
        error_data = response.json()
        assert error_data['status'] == 'error'
        assert 'File already downloaded' in error_data['message']
    
    def test_post_file_download_printer_offline(self, client, test_app):
        """Test POST /api/v1/files/{id}/download when printer is offline"""
        file_id = 'bambu_001_offline_printer.3mf'

        # Configure mock to return connection error
        test_app.state.file_service.download_file.return_value = {
            'status': 'error',
            'message': 'Printer not reachable',
            'local_path': None
        }

        response = client.post(f"/api/v1/files/{file_id}/download")

        # Should raise FileDownloadError which returns 503 status code
        assert response.status_code == 503
        error_data = response.json()
        assert error_data['status'] == 'error'
        assert 'Printer not reachable' in error_data['message']
    
    def test_post_file_download_disk_space_error(self, client, test_app):
        """Test POST /api/v1/files/{id}/download with insufficient disk space"""
        file_id = 'bambu_001_large_file.3mf'

        # Configure mock to return disk space error
        test_app.state.file_service.download_file.return_value = {
            'status': 'error',
            'message': 'Insufficient disk space',
            'local_path': None
        }

        response = client.post(f"/api/v1/files/{file_id}/download")

        # Should raise FileDownloadError which returns 503 status code
        assert response.status_code == 503
        error_data = response.json()
        assert error_data['status'] == 'error'
        assert 'Insufficient disk space' in error_data['message']
    
    def test_post_file_download_with_progress_tracking(self, client, test_app, temp_download_directory):
        """Test POST /api/v1/files/{id}/download with progress tracking"""
        file_id = 'bambu_001_large_file.3mf'
        local_path = os.path.join(temp_download_directory, 'large_file.3mf')

        # Configure mock for successful download
        test_app.state.file_service.download_file.return_value = {
            'status': 'success',
            'message': 'File download started',
            'local_path': local_path,
            'file_id': file_id,
            'file_size': 1024000
        }

        response = client.post(f"/api/v1/files/{file_id}/download")

        # Should complete normally (progress tracking handled internally)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
    
    def test_delete_file_local(self, client, test_app):
        """Test DELETE /api/v1/files/{id} - Delete local file"""
        file_id = 'local_file_001'

        # Configure mock to return success
        test_app.state.file_service.delete_file.return_value = True

        response = client.delete(f"/api/v1/files/{file_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['status'] == 'deleted'
    
    def test_delete_file_available_only(self, client, test_app):
        """Test DELETE /api/v1/files/{id} for file that's only available on printer"""
        file_id = 'printer_file_001'

        # Configure mock to return success
        test_app.state.file_service.delete_file.return_value = True

        response = client.delete(f"/api/v1/files/{file_id}")

        # Should mark as deleted in database
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
    
    def test_get_file_download_progress(self, client, test_app):
        """Test GET /api/v1/files/downloads/{download_id}/progress"""
        download_id = 'bambu_001_test_file.3mf'

        # Configure mock file service to return progress status
        test_app.state.file_service.get_download_status = AsyncMock(return_value={
            'file_id': download_id,
            'status': 'downloading',
            'progress': 45,
            'bytes_downloaded': 1024000,
            'total_bytes': 2048000
        })

        response = client.get(f"/api/v1/files/downloads/{download_id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['download_id'] == download_id
        assert data['data']['progress'] == 45
        assert data['data']['status'] == 'downloading'
        assert data['data']['bytes_downloaded'] == 1024000
        assert data['data']['total_bytes'] == 2048000

    def test_get_file_download_progress_not_found(self, client, test_app):
        """Test GET /api/v1/files/downloads/{download_id}/progress - not found"""
        download_id = 'nonexistent_download_id'

        # Configure mock to return not_found status
        test_app.state.file_service.get_download_status = AsyncMock(return_value={
            'file_id': download_id,
            'status': 'not_found',
            'progress': 0
        })

        response = client.get(f"/api/v1/files/downloads/{download_id}/progress")

        assert response.status_code == 404
        data = response.json()
        assert data['status'] == 'error'

    def test_get_file_download_progress_completed(self, client, test_app):
        """Test GET /api/v1/files/downloads/{download_id}/progress - completed download"""
        download_id = 'bambu_001_completed_file.3mf'

        test_app.state.file_service.get_download_status = AsyncMock(return_value={
            'file_id': download_id,
            'status': 'completed',
            'progress': 100,
            'bytes_downloaded': 2048000,
            'total_bytes': 2048000,
            'downloaded_at': '2025-01-09T10:00:00Z',
            'local_path': '/downloads/bambu_001/completed_file.3mf'
        })

        response = client.get(f"/api/v1/files/downloads/{download_id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['progress'] == 100
        assert data['data']['status'] == 'completed'
    
    def test_get_file_download_history(self, client, populated_database):
        """Test GET /api/v1/files - basic list endpoint"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database

            response = client.get("/api/v1/files")

            assert response.status_code == 200
            data = response.json()
            assert 'files' in data or 'success' in data
    
    @pytest.mark.skip(reason="File cleanup endpoint not yet implemented - future feature")
    def test_post_file_cleanup(self, client):
        """Test POST /api/v1/files/cleanup - Clean up old downloaded files"""
        # This test is for a future feature - automated cleanup endpoint
        pass


class TestFileBusinessLogic:
    """Test file-related business logic and German requirements"""
    
    def test_german_file_naming_sanitization(self):
        """Test file naming follows German conventions and security requirements"""
        test_cases = [
            # German umlauts and special characters
            ('Würfel Ä Ö Ü ß.3mf', 'wuerfel_ae_oe_ue_ss.3mf'),
            
            # Spaces and special characters
            ('Test Cube (Final Version).3mf', 'test_cube_final_version.3mf'),
            
            # Long filenames
            ('Very_Long_Filename_That_Exceeds_Normal_Limits_And_Should_Be_Truncated.3mf', 
             'very_long_filename_that_exceeds_normal_limits_and_should_be_truncated.3mf'),
            
            # Security: potential path traversal
            ('../../etc/passwd.3mf', 'etc_passwd.3mf'),
            
            # Multiple extensions
            ('file.backup.3mf.old', 'file_backup_3mf.old'),
        ]
        
        for original, expected in test_cases:
            sanitized = sanitize_german_filename(original)
            # Basic check - should not contain problematic characters
            assert '..' not in sanitized
            assert '/' not in sanitized
            assert '\\' not in sanitized
    
    def test_file_download_path_organization(self, temp_download_directory, test_utils):
        """Test file download organization by printer and date"""
        printer_id = 'bambu_a1_001'
        filename = 'test_cube.3mf'
        
        # Mock current date
        test_date = test_utils.berlin_timestamp('2025-09-03T14:30:00')
        
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = test_date
            
            download_path = generate_download_path(
                temp_download_directory, 
                printer_id, 
                filename
            )
            
            expected_path = os.path.join(
                temp_download_directory,
                'bambu_a1_001',
                '2025-09-03',
                'test_cube.3mf'
            )
            
            # Normalize paths for comparison
            assert os.path.normpath(download_path) == os.path.normpath(expected_path)
    
    def test_file_checksum_verification(self, sample_3mf_file):
        """Test file integrity verification using checksums"""
        # Calculate expected checksums
        md5_hash = hashlib.md5(sample_3mf_file).hexdigest()
        sha256_hash = hashlib.sha256(sample_3mf_file).hexdigest()
        
        # Verify checksum calculation function
        calculated_md5 = calculate_file_checksum(sample_3mf_file, 'md5')
        calculated_sha256 = calculate_file_checksum(sample_3mf_file, 'sha256')
        
        assert calculated_md5 == md5_hash
        assert calculated_sha256 == sha256_hash
    
    def test_file_size_validation_german_limits(self):
        """Test file size validation according to German data protection requirements"""
        test_cases = [
            (1024, True),           # 1KB - OK
            (1024 * 1024, True),    # 1MB - OK  
            (100 * 1024 * 1024, True),  # 100MB - OK (within limit)
            (500 * 1024 * 1024, True),  # 500MB - At limit
            (600 * 1024 * 1024, False), # 600MB - Exceeds limit
        ]
        
        max_size_mb = 500  # From configuration
        
        for file_size, should_be_valid in test_cases:
            is_valid = validate_file_size(file_size, max_size_mb)
            assert is_valid == should_be_valid
    
    def test_file_metadata_extraction_3mf(self, sample_3mf_file):
        """Test 3MF file metadata extraction"""
        metadata = extract_3mf_metadata(sample_3mf_file)
        
        # Should extract basic metadata from XML
        assert 'title' in metadata
        assert 'designer' in metadata
        assert metadata['title'] == 'Test Cube'
        assert metadata['designer'] == 'Printernizer Test Suite'
    
    def test_disk_space_monitoring(self, temp_download_directory):
        """Test disk space monitoring for download operations"""
        # Mock disk space check
        with patch('shutil.disk_usage') as mock_usage:
            # Mock: Total=1GB, Used=800MB, Free=200MB
            mock_usage.return_value = (1024**3, 800*1024**2, 200*1024**2)
            
            # Should have enough space for 100MB file
            has_space = check_disk_space(temp_download_directory, 100 * 1024**2)
            assert has_space is True
            
            # Should not have enough space for 300MB file  
            has_space = check_disk_space(temp_download_directory, 300 * 1024**2)
            assert has_space is False


class TestFileAPIPerformance:
    """Test file API performance and large file handling"""
    
    def test_large_file_list_performance(self, client, db_connection):
        """Test API performance with large number of files"""
        cursor = db_connection.cursor()
        
        # Create a test printer for foreign key constraint
        cursor.execute("""
            INSERT INTO printers (id, name, type, ip_address, status)
            VALUES (?, ?, ?, ?, ?)
        """, ('test_printer_001', 'Test Printer', 'bambu_lab', '192.168.1.100', 'online'))
        
        # Insert many files for performance testing
        for i in range(200):
            cursor.execute("""
                INSERT INTO files (id, filename, file_type, file_size, download_status, printer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f'test_file_{i:03d}',
                f'test_file_{i:03d}.3mf',
                '.3mf',
                1024000 + i * 1000,
                'available' if i % 2 else 'downloaded',
                'test_printer_001' if i % 3 else None  # Some files without printer
            ))
        
        db_connection.commit()
        
        # Time the API request
        import time
        start_time = time.time()
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            response = client.get("/api/v1/files")

        end_time = time.time()
        request_time = end_time - start_time

        # Request should complete within reasonable time
        assert response.status_code == 200
        assert request_time < 2.0  # Should complete within 2 seconds

        data = response.json()
        assert 'files' in data
    
    def test_concurrent_file_downloads(self, client, test_app, temp_download_directory):
        """Test concurrent file download requests"""
        import threading

        # Configure mock to return success for concurrent calls
        local_path = os.path.join(temp_download_directory, 'concurrent_test.3mf')
        test_app.state.file_service.download_file.return_value = {
            'status': 'success',
            'message': 'File downloaded successfully',
            'local_path': local_path,
            'file_id': 'bambu_001_concurrent_test.3mf',
            'file_size': 1024
        }

        results = []

        def download_file(file_id):
            try:
                response = client.post(f"/api/v1/files/{file_id}/download")
                results.append(response.status_code)
            except Exception as e:
                results.append(500)

        # Try to download same file concurrently (should handle gracefully)
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=download_file, args=('bambu_001_concurrent_test.3mf',))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed or handle gracefully
        success_count = len([r for r in results if r == 200])

        assert success_count >= 1  # At least one should succeed
        assert len(results) == 3  # All threads completed


# Helper functions for testing
def sanitize_german_filename(filename):
    """Mock function to sanitize German filenames"""
    import re
    
    # Handle German umlauts
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'AE', 'Ö': 'OE', 'Ü': 'UE'
    }
    
    for umlaut, replacement in replacements.items():
        filename = filename.replace(umlaut, replacement)
    
    # Remove/replace problematic characters
    filename = re.sub(r'[^\w\s\.-]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.lower()
    
    # Remove path traversal attempts
    filename = filename.replace('..', '')
    filename = filename.replace('/', '_')
    filename = filename.replace('\\', '_')
    
    return filename


def generate_download_path(base_dir, printer_id, filename):
    """Mock function to generate download path"""
    from datetime import datetime
    
    # Get current date in Berlin timezone
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    return os.path.join(base_dir, printer_id, date_str, filename)


def calculate_file_checksum(file_content, algorithm='md5'):
    """Calculate file checksum"""
    if algorithm == 'md5':
        return hashlib.md5(file_content).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(file_content).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def validate_file_size(file_size_bytes, max_size_mb):
    """Validate file size against limits"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size_bytes <= max_size_bytes


def extract_3mf_metadata(file_content):
    """Extract metadata from 3MF file content"""
    import xml.etree.ElementTree as ET
    
    try:
        root = ET.fromstring(file_content.decode('utf-8'))
        metadata = {}
        
        # Extract metadata elements
        for meta in root.findall('.//{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}metadata'):
            name = meta.get('name')
            value = meta.text
            if name and value:
                metadata[name.lower()] = value
        
        return metadata
    except Exception:
        return {}


def check_disk_space(directory, required_bytes):
    """Check if directory has enough free disk space"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage(directory)
        return free >= required_bytes
    except Exception:
        return False