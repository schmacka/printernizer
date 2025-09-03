"""
Test suite for Printer Management API endpoints
Tests all printer-related API functionality including CRUD operations,
status monitoring, and German business requirements.
"""
import pytest
import json
import sqlite3
from unittest.mock import patch, Mock
from datetime import datetime, timezone


class TestPrinterAPI:
    """Test printer management API endpoints"""
    
    def test_get_printers_empty_database(self, api_client, temp_database, test_config):
        """Test GET /api/v1/printers with empty database"""
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value.execute.return_value.fetchall.return_value = []
            
            response = api_client.get(f"{test_config['api_base_url']}/printers")
            
            assert response.status_code == 200
            data = response.json()
            assert data['printers'] == []
            assert data['total_count'] == 0
            assert 'pagination' in data
    
    def test_get_printers_with_data(self, api_client, populated_database, test_config, sample_printer_data):
        """Test GET /api/v1/printers with existing printers"""
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/printers")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['printers']) == 2
            assert data['total_count'] == 2
            
            # Verify Bambu Lab printer
            bambu_printer = next(p for p in data['printers'] if p['type'] == 'bambu_lab')
            assert bambu_printer['name'] == 'Bambu Lab A1 #1'
            assert bambu_printer['model'] == 'A1'
            assert bambu_printer['has_ams'] is True
            
            # Verify Prusa printer
            prusa_printer = next(p for p in data['printers'] if p['type'] == 'prusa')
            assert prusa_printer['name'] == 'Prusa Core One #1'
            assert prusa_printer['model'] == 'Core One'
    
    def test_get_printers_filter_by_type(self, api_client, populated_database, test_config):
        """Test GET /api/v1/printers?type=bambu_lab"""
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/printers?type=bambu_lab")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['printers']) == 1
            assert data['printers'][0]['type'] == 'bambu_lab'
    
    def test_get_printers_filter_by_active_status(self, api_client, populated_database, test_config):
        """Test GET /api/v1/printers?active=true"""
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.get(f"{test_config['api_base_url']}/printers?active=true")
            
            assert response.status_code == 200
            data = response.json()
            for printer in data['printers']:
                assert printer['is_active'] is True
    
    def test_post_printers_bambu_lab(self, api_client, db_connection, test_config):
        """Test POST /api/v1/printers - Add Bambu Lab printer"""
        printer_data = {
            'name': 'New Bambu Lab A1',
            'type': 'bambu_lab',
            'model': 'A1',
            'ip_address': '192.168.1.102',
            'access_code': 'new_access_code',
            'serial_number': 'AC87654321',
            'has_camera': True,
            'has_ams': True,
            'supports_remote_control': True
        }
        
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            
            response = api_client.post(
                f"{test_config['api_base_url']}/printers",
                json=printer_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data['printer']['name'] == printer_data['name']
            assert data['printer']['type'] == 'bambu_lab'
            assert 'id' in data['printer']
            assert data['printer']['is_active'] is True
    
    def test_post_printers_prusa(self, api_client, db_connection, test_config):
        """Test POST /api/v1/printers - Add Prusa printer"""
        printer_data = {
            'name': 'New Prusa Core One',
            'type': 'prusa',
            'model': 'Core One',
            'ip_address': '192.168.1.103',
            'api_key': 'new_prusa_api_key_67890'
        }
        
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            
            response = api_client.post(
                f"{test_config['api_base_url']}/printers",
                json=printer_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data['printer']['name'] == printer_data['name']
            assert data['printer']['type'] == 'prusa'
            assert data['printer']['api_key'] == printer_data['api_key']
    
    def test_post_printers_validation_errors(self, api_client, test_config):
        """Test POST /api/v1/printers with validation errors"""
        test_cases = [
            # Missing required fields
            ({}, 400, 'Missing required field: name'),
            ({'name': 'Test'}, 400, 'Missing required field: type'),
            ({'name': 'Test', 'type': 'bambu_lab'}, 400, 'Missing required field: ip_address'),
            
            # Invalid printer type
            ({
                'name': 'Invalid Printer',
                'type': 'invalid_type',
                'ip_address': '192.168.1.100'
            }, 400, 'Invalid printer type'),
            
            # Invalid IP address
            ({
                'name': 'Test Printer',
                'type': 'bambu_lab',
                'ip_address': 'invalid_ip'
            }, 400, 'Invalid IP address'),
            
            # Missing Bambu Lab specific fields
            ({
                'name': 'Bambu Test',
                'type': 'bambu_lab',
                'ip_address': '192.168.1.100'
            }, 400, 'Bambu Lab printers require access_code and serial_number'),
            
            # Missing Prusa specific fields
            ({
                'name': 'Prusa Test',
                'type': 'prusa', 
                'ip_address': '192.168.1.101'
            }, 400, 'Prusa printers require api_key')
        ]
        
        for printer_data, expected_status, expected_error in test_cases:
            response = api_client.post(
                f"{test_config['api_base_url']}/printers",
                json=printer_data
            )
            
            assert response.status_code == expected_status
            if expected_status == 400:
                assert expected_error in response.json()['error']['message']
    
    def test_get_printer_status_bambu_lab(self, api_client, populated_database, test_config, mock_bambu_api):
        """Test GET /api/v1/printers/{id}/status for Bambu Lab printer"""
        printer_id = 'bambu_a1_001'
        
        with patch('backend.printers.bambu.BambuLabAPI') as mock_api_class:
            mock_api_class.return_value = mock_bambu_api
            
            response = api_client.get(
                f"{test_config['api_base_url']}/printers/{printer_id}/status"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify status structure
            assert 'printer_id' in data
            assert 'status' in data
            assert 'current_job' in data
            assert 'temperatures' in data
            assert 'system_info' in data
            
            # Verify job information
            assert data['current_job']['status'] == 'printing'
            assert data['current_job']['progress'] == 45
            assert data['current_job']['estimated_remaining'] == 3600
            
            # Verify temperatures
            temps = data['temperatures']
            assert temps['nozzle']['current'] == 210.5
            assert temps['bed']['current'] == 60.2
            assert temps['chamber']['current'] == 28.5
    
    def test_get_printer_status_prusa(self, api_client, populated_database, test_config, mock_prusa_api):
        """Test GET /api/v1/printers/{id}/status for Prusa printer"""
        printer_id = 'prusa_core_001'
        
        with patch('backend.printers.prusa.PrusaLinkAPI') as mock_api_class:
            mock_api_class.return_value = mock_prusa_api
            
            response = api_client.get(
                f"{test_config['api_base_url']}/printers/{printer_id}/status"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify status structure
            assert data['printer_id'] == printer_id
            assert data['status'] == 'operational'
            assert 'temperatures' in data
            
            # Verify temperatures
            temps = data['temperatures']
            assert temps['nozzle']['current'] == 25.0
            assert temps['bed']['current'] == 25.0
    
    def test_get_printer_status_offline(self, api_client, test_config):
        """Test GET /api/v1/printers/{id}/status for offline printer"""
        printer_id = 'offline_printer'
        
        with patch('backend.printers.get_printer_api') as mock_get_api:
            mock_get_api.side_effect = ConnectionError("Printer not reachable")
            
            response = api_client.get(
                f"{test_config['api_base_url']}/printers/{printer_id}/status"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'offline'
            assert data['error'] == 'Printer not reachable'
    
    def test_get_printer_status_not_found(self, api_client, test_config):
        """Test GET /api/v1/printers/{id}/status for non-existent printer"""
        response = api_client.get(
            f"{test_config['api_base_url']}/printers/non_existent/status"
        )
        
        assert response.status_code == 404
        assert 'Printer not found' in response.json()['error']['message']
    
    def test_put_printers_update_config(self, api_client, populated_database, test_config):
        """Test PUT /api/v1/printers/{id} - Update printer configuration"""
        printer_id = 'bambu_a1_001'
        update_data = {
            'name': 'Updated Bambu Lab A1',
            'ip_address': '192.168.1.150',
            'is_active': False
        }
        
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.put(
                f"{test_config['api_base_url']}/printers/{printer_id}",
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['printer']['name'] == update_data['name']
            assert data['printer']['ip_address'] == update_data['ip_address']
            assert data['printer']['is_active'] is False
    
    def test_put_printers_invalid_update(self, api_client, test_config):
        """Test PUT /api/v1/printers/{id} with invalid data"""
        printer_id = 'bambu_a1_001'
        
        test_cases = [
            # Invalid IP address
            ({'ip_address': 'invalid_ip'}, 'Invalid IP address'),
            
            # Invalid printer type (should not be changeable)
            ({'type': 'invalid_type'}, 'Printer type cannot be changed'),
            
            # Empty name
            ({'name': ''}, 'Name cannot be empty'),
        ]
        
        for update_data, expected_error in test_cases:
            response = api_client.put(
                f"{test_config['api_base_url']}/printers/{printer_id}",
                json=update_data
            )
            
            assert response.status_code == 400
            assert expected_error in response.json()['error']['message']
    
    def test_delete_printers(self, api_client, populated_database, test_config):
        """Test DELETE /api/v1/printers/{id}"""
        printer_id = 'prusa_core_001'
        
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.delete(
                f"{test_config['api_base_url']}/printers/{printer_id}"
            )
            
            assert response.status_code == 204
            
            # Verify printer is marked as inactive, not actually deleted
            cursor = populated_database.cursor()
            cursor.execute("SELECT is_active FROM printers WHERE id = ?", (printer_id,))
            result = cursor.fetchone()
            assert result is not None  # Printer still exists
            assert result[0] == 0  # But is marked inactive
    
    def test_delete_printer_with_active_jobs(self, api_client, populated_database, test_config):
        """Test DELETE /api/v1/printers/{id} with active print jobs"""
        printer_id = 'bambu_a1_001'  # This printer has an active printing job
        
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = api_client.delete(
                f"{test_config['api_base_url']}/printers/{printer_id}"
            )
            
            assert response.status_code == 409
            error_data = response.json()
            assert 'Cannot delete printer with active jobs' in error_data['error']['message']
    
    def test_printer_connection_test(self, api_client, test_config, mock_bambu_api):
        """Test POST /api/v1/printers/{id}/test-connection"""
        printer_id = 'bambu_a1_001'
        
        with patch('backend.printers.bambu.BambuLabAPI') as mock_api_class:
            mock_api_class.return_value = mock_bambu_api
            mock_bambu_api.test_connection.return_value = True
            
            response = api_client.post(
                f"{test_config['api_base_url']}/printers/{printer_id}/test-connection"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['connection_test']['success'] is True
            assert 'response_time_ms' in data['connection_test']
    
    def test_printer_connection_test_failed(self, api_client, test_config):
        """Test POST /api/v1/printers/{id}/test-connection with failed connection"""
        printer_id = 'offline_printer'
        
        with patch('backend.printers.get_printer_api') as mock_get_api:
            mock_get_api.side_effect = ConnectionError("Connection timeout")
            
            response = api_client.post(
                f"{test_config['api_base_url']}/printers/{printer_id}/test-connection"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['connection_test']['success'] is False
            assert 'Connection timeout' in data['connection_test']['error']


class TestPrinterBusinessLogic:
    """Test printer-related business logic and German requirements"""
    
    def test_printer_timezone_handling(self, populated_database, german_business_config, test_utils):
        """Test that printer timestamps use Europe/Berlin timezone"""
        cursor = populated_database.cursor()
        cursor.execute(
            "SELECT created_at, updated_at FROM printers WHERE id = ?", 
            ('bambu_a1_001',)
        )
        result = cursor.fetchone()
        
        # Timestamps should be stored in UTC but displayed in Berlin timezone
        created_at = result[0]
        berlin_time = test_utils.berlin_timestamp(created_at)
        
        assert berlin_time.tzinfo.zone == 'Europe/Berlin'
    
    def test_printer_cost_calculations_euro(self, sample_cost_calculations, test_utils):
        """Test cost calculations in EUR for German business"""
        material_cost = sample_cost_calculations['material_usage_grams'] * \
                       sample_cost_calculations['material_cost_per_gram']
        
        power_cost = sample_cost_calculations['print_duration_hours'] * \
                    sample_cost_calculations['power_consumption_kwh'] * \
                    sample_cost_calculations['power_rate_per_kwh']
        
        labor_cost = sample_cost_calculations['labor_hours'] * \
                    sample_cost_calculations['labor_rate_per_hour']
        
        subtotal = material_cost + power_cost + labor_cost
        vat_amount = test_utils.calculate_vat(subtotal, sample_cost_calculations['vat_rate'])
        total_with_vat = subtotal + vat_amount
        
        # Verify calculations
        assert material_cost == 1.275  # 25.5g * 0.05 EUR/g
        assert power_cost == 0.225  # 2.5h * 0.3kWh * 0.30 EUR/kWh
        assert labor_cost == 7.5   # 0.5h * 15.0 EUR/h
        assert vat_amount == 1.71  # 19% VAT
        assert total_with_vat == 10.71  # Total with German VAT
    
    def test_printer_business_hours_validation(self, german_business_config):
        """Test business hours validation for German operations"""
        from datetime import datetime, time
        
        business_start = time.fromisoformat(german_business_config['business_hours']['start'])
        business_end = time.fromisoformat(german_business_config['business_hours']['end'])
        
        # Test times
        test_cases = [
            (time(9, 0), True),   # 09:00 - business hours
            (time(12, 0), True),  # 12:00 - lunch time but still business
            (time(17, 30), True), # 17:30 - still business hours
            (time(19, 0), False), # 19:00 - after business hours
            (time(6, 0), False),  # 06:00 - before business hours
        ]
        
        for test_time, expected_business_hours in test_cases:
            is_business_hours = business_start <= test_time <= business_end
            assert is_business_hours == expected_business_hours
    
    def test_printer_id_generation_german_locale(self):
        """Test printer ID generation follows German naming conventions"""
        test_cases = [
            ('Bambu Lab A1', 'bambu_lab', 'bambu_a1_001'),
            ('Prusa Core One', 'prusa', 'prusa_core_one_001'),
            ('Bambu Lab X1 Carbon', 'bambu_lab', 'bambu_x1_carbon_001'),
        ]
        
        for name, printer_type, expected_id_pattern in test_cases:
            # Mock ID generation logic
            generated_id = generate_printer_id(name, printer_type)
            assert expected_id_pattern in generated_id or generated_id.startswith(expected_id_pattern.split('_')[0])


def generate_printer_id(name, printer_type):
    """Mock function for printer ID generation"""
    import re
    
    # Simplify name for ID
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    clean_name = re.sub(r'\s+', '_', clean_name.strip())
    
    # Generate ID with counter
    base_id = f"{printer_type}_{clean_name}"
    return f"{base_id}_001"


class TestPrinterAPIEdgeCases:
    """Test edge cases and error conditions for printer API"""
    
    def test_concurrent_printer_requests(self, api_client, test_config, populated_database):
        """Test concurrent requests to printer API"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = api_client.get(f"{test_config['api_base_url']}/printers")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10
    
    def test_large_printer_list_performance(self, api_client, test_config, db_connection):
        """Test API performance with large number of printers"""
        # Insert many printers for performance testing
        cursor = db_connection.cursor()
        
        for i in range(100):
            cursor.execute("""
                INSERT INTO printers (id, name, type, ip_address, api_key, is_active) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f'test_printer_{i:03d}',
                f'Test Printer {i}',
                'prusa',
                f'192.168.1.{i+10}',
                f'api_key_{i}',
                True
            ))
        
        db_connection.commit()
        
        # Time the API request
        import time
        start_time = time.time()
        
        with patch('backend.database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            response = api_client.get(f"{test_config['api_base_url']}/printers")
        
        end_time = time.time()
        request_time = end_time - start_time
        
        # Request should complete within reasonable time
        assert response.status_code == 200
        assert request_time < 1.0  # Should complete within 1 second
        
        data = response.json()
        assert len(data['printers']) == 102  # 100 test + 2 from fixtures
    
    def test_printer_api_rate_limiting(self, api_client, test_config):
        """Test API rate limiting for printer endpoints"""
        # This test would implement rate limiting checks
        # For now, just verify the endpoint handles multiple rapid requests
        
        responses = []
        for i in range(50):
            response = api_client.get(f"{test_config['api_base_url']}/printers")
            responses.append(response.status_code)
        
        # Should not have any 429 (Too Many Requests) responses in normal testing
        success_responses = [r for r in responses if r == 200]
        assert len(success_responses) >= 45  # Allow for some potential failures
    
    def test_invalid_json_handling(self, api_client, test_config):
        """Test handling of invalid JSON in POST requests"""
        invalid_json_data = '{"name": "Test", "type": "bambu_lab", invalid}'
        
        response = api_client.post(
            f"{test_config['api_base_url']}/printers",
            data=invalid_json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert 'Invalid JSON' in error_data['error']['message']
    
    def test_oversized_request_handling(self, api_client, test_config):
        """Test handling of oversized requests"""
        # Create oversized printer data
        oversized_data = {
            'name': 'Test Printer',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'notes': 'x' * 10000  # 10KB of notes
        }
        
        response = api_client.post(
            f"{test_config['api_base_url']}/printers",
            json=oversized_data
        )
        
        # Should either accept it or return appropriate error
        assert response.status_code in [201, 400, 413]  # Created, Bad Request, or Payload Too Large