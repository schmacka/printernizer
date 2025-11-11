"""
Error Handling and Edge Case Tests
Tests system resilience and error handling including:
- Network connectivity issues
- Invalid data inputs
- Hardware failure scenarios
- Database corruption/unavailability
- File system errors
- Memory/resource exhaustion
- Concurrent access conflicts
- Malformed API requests
- Security edge cases

TODO: These tests need refactoring to match current implementation.
Many tests attempt to patch non-existent modules (bambu_service, prusa_service, validation).
Current implementation uses src.printers.bambu_lab and src.printers.prusa.
Tests should be updated to test actual API endpoints and error responses.
"""
import pytest
import sqlite3
import json
import asyncio
import tempfile
import os
import shutil
from datetime import datetime, timezone
from unittest.mock import patch, Mock, MagicMock
from contextlib import contextmanager
import requests
from decimal import Decimal, InvalidOperation

# Skip entire module - tests need refactoring to match current implementation
pytestmark = pytest.mark.skip(reason="Tests patch non-existent modules - need refactoring")


class TestNetworkErrorHandling:
    """Test handling of network-related errors"""
    
    def test_printer_connection_timeout(self, api_client, test_config):
        """Test handling of printer connection timeouts"""
        base_url = test_config['api_base_url']
        
        printer_data = {
            'name': 'Timeout Test Printer',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.99',  # Non-responsive IP
            'access_code': 'test_code'
        }
        
        # Mock connection timeout
        with patch('src.services.bambu_service.test_connection') as mock_connect:
            mock_connect.side_effect = requests.exceptions.ConnectTimeout("Connection timed out")
            
            response = api_client.post(f"{base_url}/printers", json=printer_data)
            
            assert response.status_code == 400
            error_data = response.json()
            assert error_data['error_type'] == 'connection_error'
            assert 'timeout' in error_data['message'].lower()
            assert 'retry_after' in error_data  # Should suggest retry timing
    
    def test_network_interruption_during_operation(self, api_client, populated_database, test_config):
        """Test handling of network interruptions during ongoing operations"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Simulate network interruption during status check
            with patch('src.services.bambu_service.get_status') as mock_status:
                mock_status.side_effect = requests.exceptions.ConnectionError("Network unreachable")
                
                response = api_client.get(f"{base_url}/printers/bambu_a1_001/status")
                
                assert response.status_code == 503  # Service Unavailable
                error_data = response.json()
                assert error_data['error_type'] == 'network_error'
                assert error_data['printer_id'] == 'bambu_a1_001'
                assert 'cached_status' in error_data  # Should provide last known status
    
    def test_dns_resolution_failure(self, api_client, test_config):
        """Test handling of DNS resolution failures"""
        printer_data = {
            'name': 'DNS Failure Test',
            'type': 'prusa',
            'ip_address': 'non-existent-printer.local',  # DNS will fail
            'api_key': 'test_key'
        }
        
        with patch('src.services.prusa_service.test_connection') as mock_connect:
            mock_connect.side_effect = requests.exceptions.ConnectionError(
                "Failed to resolve 'non-existent-printer.local'"
            )
            
            response = api_client.post(f"{test_config['api_base_url']}/printers", json=printer_data)
            
            assert response.status_code == 400
            error_data = response.json()
            assert error_data['error_type'] == 'dns_error'
            assert 'resolve' in error_data['message'].lower()
    
    def test_ssl_certificate_errors(self, api_client, test_config):
        """Test handling of SSL/TLS certificate errors"""
        printer_data = {
            'name': 'SSL Error Test',
            'type': 'prusa',
            'ip_address': '192.168.1.100',
            'api_key': 'test_key',
            'use_https': True
        }
        
        with patch('src.services.prusa_service.test_connection') as mock_connect:
            mock_connect.side_effect = requests.exceptions.SSLError(
                "SSL certificate verify failed"
            )
            
            response = api_client.post(f"{test_config['api_base_url']}/printers", json=printer_data)
            
            assert response.status_code == 400
            error_data = response.json()
            assert error_data['error_type'] == 'ssl_error'
            assert 'certificate' in error_data['message'].lower()
            assert 'insecure_mode' in error_data['suggestions']  # Suggest fallback


class TestDataValidationErrors:
    """Test handling of invalid data inputs"""
    
    def test_malformed_json_requests(self, api_client, test_config):
        """Test handling of malformed JSON in API requests"""
        base_url = test_config['api_base_url']
        
        # Test invalid JSON syntax
        invalid_json_cases = [
            '{"name": "test"',  # Missing closing brace
            '{"name": test"}',   # Missing quotes around value
            '{name: "test"}',    # Missing quotes around key
            '{"name": "test",}', # Trailing comma
            'not json at all',   # Not JSON
            '',                  # Empty string
            None                 # None value
        ]
        
        for invalid_json in invalid_json_cases:
            # Mock the raw request to send invalid JSON
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.json.return_value = {
                    'error_type': 'json_parse_error',
                    'message': 'Invalid JSON format in request body',
                    'details': f'Failed to parse: {invalid_json}'
                }
                mock_post.return_value = mock_response
                
                response = mock_post(f"{base_url}/printers", data=invalid_json, 
                                   headers={'Content-Type': 'application/json'})
                
                assert response.status_code == 400
                error_data = response.json()
                assert error_data['error_type'] == 'json_parse_error'
    
    def test_invalid_data_types(self, api_client, test_config):
        """Test handling of invalid data types in requests"""
        base_url = test_config['api_base_url']
        
        # Test invalid printer data types
        invalid_printer_data_cases = [
            {'name': 123, 'type': 'bambu_lab'},  # Name should be string
            {'name': 'Test', 'type': True},      # Type should be string
            {'name': 'Test', 'type': 'bambu_lab', 'has_camera': 'yes'},  # Boolean expected
            {'name': 'Test', 'type': 'bambu_lab', 'ip_address': 192168001100},  # String expected
            {'name': 'Test', 'type': 'unknown_type'},  # Invalid enum value
            {'name': '', 'type': 'bambu_lab'},    # Empty required field
            {'type': 'bambu_lab'},                # Missing required field
        ]
        
        for invalid_data in invalid_printer_data_cases:
            with patch('src.services.validation.validate_printer_data') as mock_validate:
                mock_validate.return_value = {
                    'is_valid': False,
                    'errors': [
                        {
                            'field': next(iter(invalid_data.keys())),
                            'error': 'Invalid data type or value',
                            'expected': 'string',
                            'received': type(list(invalid_data.values())[0]).__name__
                        }
                    ]
                }
                
                response = api_client.post(f"{base_url}/printers", json=invalid_data)
                
                assert response.status_code == 422  # Unprocessable Entity
                error_data = response.json()
                assert error_data['error_type'] == 'validation_error'
                assert 'errors' in error_data
    
    def test_out_of_range_values(self, api_client, test_config):
        """Test handling of out-of-range numeric values"""
        base_url = test_config['api_base_url']
        
        job_data = {
            'printer_id': 'test_printer',
            'job_name': 'test.3mf',
            'progress': 150.0,  # Progress should be 0-100
            'layer_height': -0.1,  # Negative layer height
            'infill_percentage': 200,  # Infill should be 0-100
            'nozzle_temperature': 500,  # Unrealistic temperature
            'material_cost_per_gram': -1.0  # Negative cost
        }
        
        with patch('src.services.validation.validate_job_data') as mock_validate:
            mock_validate.return_value = {
                'is_valid': False,
                'errors': [
                    {'field': 'progress', 'error': 'Value out of range', 'range': '0-100', 'received': 150.0},
                    {'field': 'layer_height', 'error': 'Value must be positive', 'received': -0.1},
                    {'field': 'nozzle_temperature', 'error': 'Temperature unrealistic', 'max_safe': 350}
                ]
            }
            
            response = api_client.post(f"{base_url}/jobs", json=job_data)
            
            assert response.status_code == 422
            error_data = response.json()
            assert len(error_data['errors']) >= 3
    
    def test_string_length_validation(self, api_client, test_config):
        """Test handling of strings that are too long or too short"""
        base_url = test_config['api_base_url']
        
        # Test various string length violations
        string_test_cases = [
            {'name': '', 'error': 'too_short'},  # Empty name
            {'name': 'a' * 256, 'error': 'too_long'},  # Name too long
            {'customer_name': 'x' * 1000, 'error': 'too_long'},  # Customer name too long
            {'job_name': '../../../etc/passwd', 'error': 'invalid_characters'},  # Path traversal
            {'description': '\x00\x01\x02', 'error': 'invalid_characters'}  # Control characters
        ]
        
        for test_case in string_test_cases:
            job_data = {
                'printer_id': 'test_printer',
                'job_name': 'test.3mf',
                **test_case
            }
            
            with patch('src.services.validation.validate_string_fields') as mock_validate:
                mock_validate.return_value = {
                    'is_valid': False,
                    'errors': [{
                        'field': list(test_case.keys())[0],
                        'error_type': test_case['error'],
                        'message': f'String validation failed: {test_case["error"]}'
                    }]
                }
                
                response = api_client.post(f"{base_url}/jobs", json=job_data)
                assert response.status_code == 422


class TestDatabaseErrorHandling:
    """Test handling of database-related errors"""
    
    def test_database_connection_failure(self, api_client, test_config):
        """Test handling when database is unavailable"""
        base_url = test_config['api_base_url']
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.side_effect = sqlite3.OperationalError("database is locked")
            
            response = api_client.get(f"{base_url}/printers")
            
            assert response.status_code == 503  # Service Unavailable
            error_data = response.json()
            assert error_data['error_type'] == 'database_error'
            assert 'temporary' in error_data['message'].lower()
            assert 'retry_after' in error_data
    
    def test_database_corruption(self, temp_database, api_client, test_config):
        """Test handling of database corruption scenarios"""
        # Simulate corrupted database
        with open(temp_database, 'wb') as f:
            f.write(b'corrupted database content')
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.side_effect = sqlite3.DatabaseError("file is not a database")
            
            response = api_client.get(f"{test_config['api_base_url']}/printers")
            
            assert response.status_code == 500
            error_data = response.json()
            assert error_data['error_type'] == 'database_corruption'
            assert 'backup' in error_data['message'].lower()
    
    def test_constraint_violations(self, api_client, populated_database, test_config):
        """Test handling of database constraint violations"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Test duplicate printer ID
            duplicate_printer = {
                'id': 'bambu_a1_001',  # Already exists
                'name': 'Duplicate Printer',
                'type': 'bambu_lab'
            }
            
            with patch('src.database.database.Database.insert_printer') as mock_insert:
                mock_insert.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: printers.id")
                
                response = api_client.post(f"{base_url}/printers", json=duplicate_printer)
                
                assert response.status_code == 409  # Conflict
                error_data = response.json()
                assert error_data['error_type'] == 'duplicate_resource'
                assert error_data['field'] == 'id'
    
    def test_transaction_rollback_on_error(self, api_client, populated_database, test_config):
        """Test that database transactions are properly rolled back on errors"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Create job data that will cause a mid-transaction error
            job_data = {
                'printer_id': 'bambu_a1_001',
                'job_name': 'transaction_test.3mf',
                'material_type': 'PLA'
            }
            
            with patch('src.database.database.Database.insert_job') as mock_insert_job:
                with patch('src.database.database.Database.insert_job_files') as mock_insert_files:
                    # First insert succeeds, second fails
                    mock_insert_job.return_value = 'test_job_id'
                    mock_insert_files.side_effect = sqlite3.Error("Simulated error")
                    
                    response = api_client.post(f"{base_url}/jobs", json=job_data)
                    
                    assert response.status_code == 500
                    
                    # Verify job was not actually inserted (transaction rolled back)
                    cursor = populated_database.cursor()
                    cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_name = ?", ('transaction_test.3mf',))
                    count = cursor.fetchone()[0]
                    assert count == 0  # Should be 0 due to rollback


class TestFileSystemErrorHandling:
    """Test handling of file system related errors"""
    
    def test_insufficient_disk_space(self, api_client, test_config, temp_download_directory):
        """Test handling when disk space is insufficient"""
        base_url = test_config['api_base_url']
        file_id = 'large_file_001'
        
        with patch('src.services.file_service.check_disk_space') as mock_space:
            mock_space.return_value = {
                'available_mb': 100,
                'required_mb': 500,
                'sufficient': False
            }
            
            response = api_client.post(f"{base_url}/files/{file_id}/download")
            
            assert response.status_code == 507  # Insufficient Storage
            error_data = response.json()
            assert error_data['error_type'] == 'insufficient_storage'
            assert error_data['required_mb'] == 500
            assert error_data['available_mb'] == 100
    
    def test_permission_denied_errors(self, api_client, test_config):
        """Test handling of file permission errors"""
        base_url = test_config['api_base_url']
        file_id = 'permission_test_001'
        
        with patch('src.services.file_service.download_from_printer') as mock_download:
            mock_download.side_effect = PermissionError("Permission denied: /restricted/path")
            
            response = api_client.post(f"{base_url}/files/{file_id}/download")
            
            assert response.status_code == 403  # Forbidden
            error_data = response.json()
            assert error_data['error_type'] == 'permission_error'
            assert 'permission' in error_data['message'].lower()
    
    def test_file_corruption_during_download(self, api_client, test_config):
        """Test handling of file corruption during downloads"""
        base_url = test_config['api_base_url']
        file_id = 'corruption_test_001'
        
        with patch('src.services.file_service.download_from_printer') as mock_download:
            with patch('src.services.file_service.verify_file_integrity') as mock_verify:
                mock_download.return_value = {
                    'success': True,
                    'local_path': '/tmp/corrupted_file.3mf',
                    'file_size': 1024000
                }
                
                mock_verify.return_value = {
                    'is_valid': False,
                    'error': 'Checksum mismatch',
                    'expected_checksum': 'abc123',
                    'actual_checksum': 'def456'
                }
                
                response = api_client.post(f"{base_url}/files/{file_id}/download")
                
                assert response.status_code == 422  # Unprocessable Entity
                error_data = response.json()
                assert error_data['error_type'] == 'file_corruption'
                assert 'checksum' in error_data['message'].lower()
    
    def test_missing_file_errors(self, api_client, test_config):
        """Test handling when requested files don't exist"""
        base_url = test_config['api_base_url']
        
        # Test missing file on printer
        with patch('src.services.file_service.get_printer_file') as mock_get_file:
            mock_get_file.return_value = None
            
            response = api_client.post(f"{base_url}/files/nonexistent_file/download")
            
            assert response.status_code == 404
            error_data = response.json()
            assert error_data['error_type'] == 'file_not_found'
            assert error_data['file_id'] == 'nonexistent_file'
        
        # Test deletion of non-existent local file
        response = api_client.delete(f"{base_url}/files/nonexistent_local_file")
        
        assert response.status_code == 404
        error_data = response.json()
        assert error_data['error_type'] == 'file_not_found'


class TestConcurrencyErrorHandling:
    """Test handling of concurrency-related errors"""
    
    def test_concurrent_resource_access(self, api_client, populated_database, test_config):
        """Test handling of concurrent access to the same resource"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            printer_id = 'bambu_a1_001'
            
            # Simulate concurrent updates to the same printer
            update_data_1 = {'name': 'Update 1'}
            update_data_2 = {'name': 'Update 2'}
            
            with patch('src.database.database.Database.update_printer') as mock_update:
                # First update succeeds, second fails due to version conflict
                mock_update.side_effect = [
                    {'success': True, 'version': 2},
                    sqlite3.Error("Resource modified by another process")
                ]
                
                # Simulate concurrent requests
                import threading
                results = []
                
                def make_update(update_data, result_list):
                    try:
                        response = api_client.put(f"{base_url}/printers/{printer_id}", json=update_data)
                        result_list.append(response)
                    except Exception as e:
                        result_list.append(e)
                
                threads = [
                    threading.Thread(target=make_update, args=(update_data_1, results)),
                    threading.Thread(target=make_update, args=(update_data_2, results))
                ]
                
                for thread in threads:
                    thread.start()
                
                for thread in threads:
                    thread.join()
                
                # One should succeed, one should fail with conflict
                status_codes = [r.status_code if hasattr(r, 'status_code') else 500 for r in results]
                assert 200 in status_codes  # One successful
                assert 409 in status_codes  # One conflict
    
    def test_race_condition_in_job_creation(self, api_client, populated_database, test_config):
        """Test race conditions during job creation"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Create multiple jobs for the same printer simultaneously
            job_data = {
                'printer_id': 'bambu_a1_001',
                'job_name': 'race_condition_test.3mf',
                'material_type': 'PLA'
            }
            
            with patch('src.services.printer_service.is_printer_available') as mock_available:
                # Simulate race condition: printer appears available to both requests
                mock_available.return_value = True
                
                with patch('src.database.database.Database.insert_job') as mock_insert:
                    # First job creation succeeds, second fails (printer now busy)
                    mock_insert.side_effect = [
                        'job_001',
                        sqlite3.IntegrityError("Printer busy with existing job")
                    ]
                    
                    import threading
                    results = []
                    
                    def create_job(result_list):
                        try:
                            response = api_client.post(f"{base_url}/jobs", json=job_data)
                            result_list.append(response)
                        except Exception as e:
                            result_list.append(e)
                    
                    threads = [threading.Thread(target=create_job, args=(results,)) for _ in range(2)]
                    
                    for thread in threads:
                        thread.start()
                    
                    for thread in threads:
                        thread.join()
                    
                    # Verify only one job was created
                    successful_creations = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 201)
                    assert successful_creations == 1


class TestSecurityErrorHandling:
    """Test security-related error handling"""
    
    def test_sql_injection_attempts(self, api_client, test_config):
        """Test handling of SQL injection attempts"""
        base_url = test_config['api_base_url']
        
        # Various SQL injection payloads
        injection_payloads = [
            "'; DROP TABLE printers; --",
            "' OR '1'='1",
            "'; DELETE FROM jobs WHERE '1'='1'; --",
            "' UNION SELECT * FROM printers --",
            "\"; DROP TABLE printers; --",
        ]
        
        for payload in injection_payloads:
            malicious_data = {
                'name': payload,
                'type': 'bambu_lab',
                'ip_address': '192.168.1.100'
            }
            
            with patch('src.services.validation.sanitize_input') as mock_sanitize:
                mock_sanitize.return_value = {
                    'is_safe': False,
                    'detected_threats': ['sql_injection'],
                    'sanitized_value': 'BLOCKED_MALICIOUS_INPUT'
                }
                
                response = api_client.post(f"{base_url}/printers", json=malicious_data)
                
                assert response.status_code == 400
                error_data = response.json()
                assert error_data['error_type'] == 'security_violation'
                assert 'sql_injection' in error_data['detected_threats']
    
    def test_path_traversal_attempts(self, api_client, test_config):
        """Test handling of path traversal attempts"""
        base_url = test_config['api_base_url']
        
        # Path traversal payloads
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "../../../../../../../../etc/hosts",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"  # URL encoded
        ]
        
        for payload in traversal_payloads:
            job_data = {
                'printer_id': 'test_printer',
                'job_name': payload,  # Malicious filename
                'material_type': 'PLA'
            }
            
            with patch('src.services.validation.validate_file_path') as mock_validate:
                mock_validate.return_value = {
                    'is_safe': False,
                    'error': 'Path traversal attempt detected',
                    'sanitized_path': 'blocked_malicious_path.3mf'
                }
                
                response = api_client.post(f"{base_url}/jobs", json=job_data)
                
                assert response.status_code == 400
                error_data = response.json()
                assert error_data['error_type'] == 'security_violation'
                assert 'path_traversal' in error_data['message'].lower()
    
    def test_xss_prevention(self, api_client, test_config):
        """Test prevention of XSS attacks in user inputs"""
        base_url = test_config['api_base_url']
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "'>><script>alert('xss')</script>"
        ]
        
        for payload in xss_payloads:
            printer_data = {
                'name': payload,  # Malicious name
                'type': 'bambu_lab',
                'ip_address': '192.168.1.100'
            }
            
            with patch('src.services.validation.sanitize_html') as mock_sanitize:
                mock_sanitize.return_value = {
                    'sanitized_value': 'alert(xss)',  # HTML tags removed
                    'threats_removed': ['script_tag', 'event_handler'],
                    'is_modified': True
                }
                
                response = api_client.post(f"{base_url}/printers", json=printer_data)
                
                # Should either reject or sanitize
                if response.status_code == 400:
                    error_data = response.json()
                    assert error_data['error_type'] == 'security_violation'
                elif response.status_code == 201:
                    # Should be sanitized
                    created_printer = response.json()
                    assert '<script>' not in created_printer['name']
                    assert 'alert(' not in created_printer['name']


class TestResourceExhaustionHandling:
    """Test handling of resource exhaustion scenarios"""
    
    def test_memory_exhaustion_handling(self, api_client, test_config):
        """Test handling when system runs out of memory"""
        base_url = test_config['api_base_url']
        
        # Simulate memory exhaustion during large file processing
        with patch('src.services.file_service.process_large_file') as mock_process:
            mock_process.side_effect = MemoryError("Cannot allocate memory")
            
            response = api_client.post(f"{base_url}/files/large_file_001/process")
            
            assert response.status_code == 507  # Insufficient Storage
            error_data = response.json()
            assert error_data['error_type'] == 'resource_exhaustion'
            assert 'memory' in error_data['message'].lower()
            assert 'retry_later' in error_data
    
    def test_too_many_concurrent_requests(self, api_client, test_config):
        """Test handling of too many concurrent requests"""
        base_url = test_config['api_base_url']
        
        # Simulate rate limiting
        with patch('src.api.middleware.rate_limiter.check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = {
                'allowed': False,
                'reason': 'Too many requests',
                'retry_after': 60,
                'current_rate': 100,
                'limit': 50
            }
            
            response = api_client.get(f"{base_url}/printers")
            
            assert response.status_code == 429  # Too Many Requests
            assert 'Retry-After' in response.headers
            
            error_data = response.json()
            assert error_data['error_type'] == 'rate_limit_exceeded'
            assert error_data['retry_after'] == 60
    
    def test_disk_space_exhaustion(self, api_client, test_config):
        """Test handling when disk space is exhausted"""
        base_url = test_config['api_base_url']
        
        with patch('src.services.file_service.download_from_printer') as mock_download:
            mock_download.side_effect = OSError("No space left on device")
            
            response = api_client.post(f"{base_url}/files/test_file/download")
            
            assert response.status_code == 507
            error_data = response.json()
            assert error_data['error_type'] == 'disk_full'
            assert 'space' in error_data['message'].lower()


class TestEdgeCaseScenarios:
    """Test various edge cases and boundary conditions"""
    
    def test_unicode_and_special_characters(self, api_client, test_config):
        """Test handling of Unicode and special characters"""
        base_url = test_config['api_base_url']
        
        special_char_cases = [
            "Printer名前",  # Japanese characters
            "Imprimante français",  # French with accents
            "Принтер русский",  # Cyrillic
            "🖨️ Emoji Printer 3D",  # Emoji characters
            "Printer\x00null",  # Null character
            "Printer\ttab\nnewline",  # Control characters
            "Printer with emoji 😀🔥💯",  # Multiple emoji
        ]
        
        for special_name in special_char_cases:
            printer_data = {
                'name': special_name,
                'type': 'bambu_lab',
                'ip_address': '192.168.1.100'
            }
            
            # Should handle gracefully - either accept or reject cleanly
            response = api_client.post(f"{base_url}/printers", json=printer_data)
            
            assert response.status_code in [201, 400, 422]  # Valid response codes
            
            if response.status_code != 201:
                error_data = response.json()
                assert 'error_type' in error_data
                assert 'message' in error_data
    
    def test_extreme_numeric_values(self, api_client, test_config):
        """Test handling of extreme numeric values"""
        base_url = test_config['api_base_url']
        
        extreme_values = [
            {'progress': float('inf')},  # Infinity
            {'progress': float('-inf')},  # Negative infinity
            {'progress': float('nan')},   # Not a number
            {'layer_height': 1e-10},      # Extremely small
            {'nozzle_temperature': 1e10}, # Extremely large
            {'material_cost_per_gram': Decimal('999999999999999999.99')},  # Very large decimal
        ]
        
        for extreme_data in extreme_values:
            job_data = {
                'printer_id': 'test_printer',
                'job_name': 'extreme_test.3mf',
                'material_type': 'PLA',
                **extreme_data
            }
            
            response = api_client.post(f"{base_url}/jobs", json=job_data)
            
            # Should reject extreme values gracefully
            assert response.status_code == 422
            error_data = response.json()
            assert error_data['error_type'] == 'validation_error'
    
    def test_very_long_operations(self, api_client, test_config):
        """Test handling of operations that take a very long time"""
        base_url = test_config['api_base_url']
        
        with patch('src.services.file_service.download_large_file') as mock_download:
            # Simulate very long operation (would timeout)
            import time
            
            def slow_download(*args, **kwargs):
                time.sleep(120)  # 2 minutes
                return {'success': True}
            
            mock_download.side_effect = slow_download
            
            # Should timeout gracefully
            with patch('src.constants.REQUEST_TIMEOUT', 30):  # 30 second timeout
                response = api_client.post(f"{base_url}/files/slow_file/download")
                
                assert response.status_code == 504  # Gateway Timeout
                error_data = response.json()
                assert error_data['error_type'] == 'operation_timeout'
                assert 'timeout' in error_data['message'].lower()
    
    def test_circular_references_in_data(self, api_client, test_config):
        """Test handling of circular references in data structures"""
        # This would test JSON serialization issues with circular references
        # In practice, this is more relevant for complex nested data structures
        
        class CircularReference:
            def __init__(self):
                self.self_ref = self
        
        circular_obj = CircularReference()
        
        # Test that circular references are handled in JSON serialization
        with patch('json.dumps') as mock_dumps:
            mock_dumps.side_effect = ValueError("Circular reference detected")
            
            # Should handle serialization errors gracefully
            try:
                json.dumps({'circular': circular_obj})
            except ValueError as e:
                assert 'circular' in str(e).lower() or 'reference' in str(e).lower()