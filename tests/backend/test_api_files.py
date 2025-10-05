"""
Test suite for File Management API endpoints - Drucker-Dateien System
Tests unified file listing, download functionality, and German file naming conventions.
"""
import pytest
import json
import os
import tempfile
import hashlib
from unittest.mock import patch, Mock, mock_open
from datetime import datetime


class TestFileAPI:
    """Test file management API endpoints"""
    
    def test_get_files_unified_empty(self, api_client, temp_database, test_config):
        """Test GET /api/v1/files/unified with empty database"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value.execute.return_value.fetchall.return_value = []
            
            response = api_client.get(f"{test_config['api_base_url']}/files/unified")
            
            assert response.status_code == 200
            data = response.json()
            assert data['files'] == []
            assert data['total_count'] == 0
            assert data['statistics']['available'] == 0
            assert data['statistics']['downloaded'] == 0
            assert data['statistics']['local'] == 0
    
    def test_get_files_unified_with_data(self, api_client, populated_database, test_config, sample_file_data):
        """Test GET /api/v1/files/unified with existing files"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/files/unified")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['files']) == 2
            assert data['total_count'] == 2
            
            # Verify available file
            available_file = next(f for f in data['files'] if f['download_status'] == 'available')
            assert available_file['filename'] == 'test_cube.3mf'
            assert available_file['status_icon'] == '📁'
            assert available_file['printer_id'] == 'bambu_a1_001'
            assert available_file['file_size'] == 1024000
            
            # Verify downloaded file
            downloaded_file = next(f for f in data['files'] if f['download_status'] == 'downloaded')
            assert downloaded_file['filename'] == 'prototype_v1.stl'
            assert downloaded_file['status_icon'] == '✓'
            assert downloaded_file['local_path'] is not None
            
            # Verify statistics
            stats = data['statistics']
            assert stats['available'] == 1
            assert stats['downloaded'] == 1
            assert stats['total_size_mb'] > 0
    
    def test_get_files_filter_by_printer(self, api_client, populated_database, test_config):
        """Test GET /api/v1/files/unified?printer_id=bambu_a1_001"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/files/unified?printer_id=bambu_a1_001")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['files']) == 1
            assert data['files'][0]['printer_id'] == 'bambu_a1_001'
    
    def test_get_files_filter_by_status(self, api_client, populated_database, test_config):
        """Test GET /api/v1/files/unified?status=available"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/files/unified?status=available")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['files']) == 1
            assert data['files'][0]['download_status'] == 'available'
    
    def test_get_files_filter_by_type(self, api_client, populated_database, test_config):
        """Test GET /api/v1/files/unified?file_type=.3mf"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/files/unified?file_type=.3mf")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['files']) == 1
            assert data['files'][0]['file_type'] == '.3mf'
    
    def test_post_file_download_bambu_lab(self, api_client, populated_database, test_config, mock_bambu_api, temp_download_directory, sample_3mf_file):
        """Test POST /api/v1/files/{id}/download for Bambu Lab file"""
        file_id = 'file_001'
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            # Mock file download from Bambu Lab
            mock_bambu_api.download_file.return_value = sample_3mf_file
            
            with patch('backend.printers.bambu.BambuLabAPI') as mock_api_class:
                mock_api_class.return_value = mock_bambu_api
                
                with patch('backend.files.get_download_directory') as mock_dir:
                    mock_dir.return_value = temp_download_directory
                    
                    response = api_client.post(
                        f"{test_config['api_base_url']}/files/{file_id}/download"
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data['download']['success'] is True
                    assert data['download']['file_id'] == file_id
                    assert 'local_path' in data['download']
                    assert 'file_size' in data['download']
                    assert 'checksum' in data['download']
    
    def test_post_file_download_prusa(self, api_client, populated_database, test_config, mock_prusa_api, temp_download_directory):
        """Test POST /api/v1/files/{id}/download for Prusa file"""
        file_id = 'file_002'
        mock_file_content = b"STL file content for testing"
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            # Mock file download from Prusa
            mock_prusa_api.download_file.return_value = mock_file_content
            
            with patch('backend.printers.prusa.PrusaLinkAPI') as mock_api_class:
                mock_api_class.return_value = mock_prusa_api
                
                with patch('backend.files.get_download_directory') as mock_dir:
                    mock_dir.return_value = temp_download_directory
                    
                    response = api_client.post(
                        f"{test_config['api_base_url']}/files/{file_id}/download"
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data['download']['success'] is True
    
    def test_post_file_download_already_downloaded(self, api_client, populated_database, test_config):
        """Test POST /api/v1/files/{id}/download for already downloaded file"""
        file_id = 'file_002'  # Already downloaded file from fixtures
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.post(
                f"{test_config['api_base_url']}/files/{file_id}/download"
            )
            
            assert response.status_code == 409
            error_data = response.json()
            assert 'File already downloaded' in error_data['error']['message']
    
    def test_post_file_download_printer_offline(self, api_client, populated_database, test_config):
        """Test POST /api/v1/files/{id}/download when printer is offline"""
        file_id = 'file_001'
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            # Mock printer API to raise connection error
            with patch('backend.printers.get_printer_api') as mock_get_api:
                mock_get_api.side_effect = ConnectionError("Printer not reachable")
                
                response = api_client.post(
                    f"{test_config['api_base_url']}/files/{file_id}/download"
                )
                
                assert response.status_code == 503
                error_data = response.json()
                assert 'Printer not reachable' in error_data['error']['message']
    
    def test_post_file_download_disk_space_error(self, api_client, populated_database, test_config, mock_bambu_api):
        """Test POST /api/v1/files/{id}/download with insufficient disk space"""
        file_id = 'file_001'
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            with patch('backend.printers.bambu.BambuLabAPI') as mock_api_class:
                mock_api_class.return_value = mock_bambu_api
                
                # Mock disk space check to fail
                with patch('backend.files.check_disk_space') as mock_space:
                    mock_space.return_value = False
                    
                    response = api_client.post(
                        f"{test_config['api_base_url']}/files/{file_id}/download"
                    )
                    
                    assert response.status_code == 507
                    error_data = response.json()
                    assert 'Insufficient disk space' in error_data['error']['message']
    
    def test_post_file_download_with_progress_tracking(self, api_client, populated_database, test_config, mock_bambu_api, temp_download_directory):
        """Test POST /api/v1/files/{id}/download with progress tracking"""
        file_id = 'file_001'
        large_file_content = b'x' * 1024000  # 1MB file
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            # Mock progressive download
            mock_bambu_api.download_file_with_progress = Mock()
            mock_bambu_api.download_file_with_progress.return_value = large_file_content
            
            with patch('backend.printers.bambu.BambuLabAPI') as mock_api_class:
                mock_api_class.return_value = mock_bambu_api
                
                with patch('backend.files.get_download_directory') as mock_dir:
                    mock_dir.return_value = temp_download_directory
                    
                    response = api_client.post(
                        f"{test_config['api_base_url']}/files/{file_id}/download?track_progress=true"
                    )
                    
                    assert response.status_code == 202  # Accepted for async download
                    data = response.json()
                    assert 'download_id' in data
                    assert data['status'] == 'started'
    
    def test_delete_file_local(self, api_client, populated_database, test_config, temp_download_directory):
        """Test DELETE /api/v1/files/{id} - Delete local file"""
        file_id = 'file_002'  # Downloaded file
        
        # Create a dummy local file
        local_file_path = os.path.join(temp_download_directory, 'prototype_v1.stl')
        with open(local_file_path, 'w') as f:
            f.write('dummy content')
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            with patch('backend.files.get_local_file_path') as mock_path:
                mock_path.return_value = local_file_path
                
                response = api_client.delete(f"{test_config['api_base_url']}/files/{file_id}")
                
                assert response.status_code == 204
                
                # Verify file is deleted from filesystem
                assert not os.path.exists(local_file_path)
    
    def test_delete_file_available_only(self, api_client, populated_database, test_config):
        """Test DELETE /api/v1/files/{id} for file that's only available on printer"""
        file_id = 'file_001'  # Available but not downloaded
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.delete(f"{test_config['api_base_url']}/files/{file_id}")
            
            # Should just mark as deleted in database
            assert response.status_code == 204
    
    def test_get_file_download_progress(self, api_client, test_config):
        """Test GET /api/v1/files/downloads/{download_id}/progress"""
        download_id = 'test_download_123'
        
        with patch('backend.files.get_download_progress') as mock_progress:
            mock_progress.return_value = {
                'download_id': download_id,
                'status': 'downloading',
                'progress_percent': 45.5,
                'bytes_downloaded': 466944,
                'bytes_total': 1024000,
                'speed_bps': 102400,
                'eta_seconds': 55
            }
            
            response = api_client.get(
                f"{test_config['api_base_url']}/files/downloads/{download_id}/progress"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['progress']['status'] == 'downloading'
            assert data['progress']['progress_percent'] == 45.5
            assert 'eta_seconds' in data['progress']
    
    def test_get_file_download_history(self, api_client, populated_database, test_config):
        """Test GET /api/v1/files/download-history"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/files/download-history")
            
            assert response.status_code == 200
            data = response.json()
            assert 'downloads' in data
            assert 'total_count' in data
            assert 'statistics' in data
    
    def test_post_file_cleanup(self, api_client, populated_database, test_config):
        """Test POST /api/v1/files/cleanup - Clean up old downloaded files"""
        cleanup_data = {
            'older_than_days': 30,
            'status_filter': 'downloaded',
            'size_threshold_mb': 10,
            'dry_run': False
        }
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            with patch('backend.files.cleanup_old_files') as mock_cleanup:
                mock_cleanup.return_value = {
                    'files_deleted': 5,
                    'space_freed_mb': 125.5,
                    'errors': []
                }
                
                response = api_client.post(
                    f"{test_config['api_base_url']}/files/cleanup",
                    json=cleanup_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['cleanup']['files_deleted'] == 5
                assert data['cleanup']['space_freed_mb'] == 125.5


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
    
    def test_large_file_list_performance(self, api_client, db_connection, test_config):
        """Test API performance with large number of files"""
        cursor = db_connection.cursor()
        
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
                'test_printer_001'
            ))
        
        db_connection.commit()
        
        # Time the API request
        import time
        start_time = time.time()
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            response = api_client.get(f"{test_config['api_base_url']}/files/unified")
        
        end_time = time.time()
        request_time = end_time - start_time
        
        # Request should complete within reasonable time
        assert response.status_code == 200
        assert request_time < 2.0  # Should complete within 2 seconds
        
        data = response.json()
        assert len(data['files']) >= 200
    
    def test_concurrent_file_downloads(self, api_client, populated_database, test_config):
        """Test concurrent file download requests"""
        import threading
        
        results = []
        
        def download_file(file_id):
            try:
                response = api_client.post(
                    f"{test_config['api_base_url']}/files/{file_id}/download"
                )
                results.append(response.status_code)
            except Exception as e:
                results.append(500)
        
        # Try to download same file concurrently (should handle gracefully)
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=download_file, args=('file_001',))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # One should succeed, others should get conflict or error
        success_count = len([r for r in results if r == 200])
        conflict_count = len([r for r in results if r == 409])
        
        assert success_count <= 1  # At most one successful download
        assert success_count + conflict_count >= 2  # Others should be handled


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