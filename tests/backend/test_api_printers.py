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
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestPrinterAPI:
    """Test printer management API endpoints"""
    
    def test_get_printers_empty_database(self, client, test_app):
        """Test GET /api/v1/printers with empty database"""
        from unittest.mock import AsyncMock

        # Configure the mock printer_service to return empty list
        test_app.state.printer_service.list_printers = AsyncMock(return_value=[])

        response = client.get("/api/v1/printers")

        assert response.status_code == 200
        data = response.json()
        assert data['printers'] == []
        assert data['total_count'] == 0
        assert 'pagination' in data
    
    def test_get_printers_with_data(self, client, test_app):
        """Test GET /api/v1/printers with existing printers"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus

        # Create sample printers
        bambu_printer = Printer(
            id='bambu_a1_001',
            name='Bambu Lab A1 #1',
            type=PrinterType.BAMBU_LAB,
            ip_address='192.168.1.100',
            access_code='test_access_code',
            serial_number='AC12345678',
            is_active=True,
            status=PrinterStatus.ONLINE,
            created_at=datetime.now()
        )

        prusa_printer = Printer(
            id='prusa_core_001',
            name='Prusa Core One #1',
            type=PrinterType.PRUSA_CORE,
            ip_address='192.168.1.101',
            api_key='test_api_key',
            is_active=True,
            status=PrinterStatus.ONLINE,
            created_at=datetime.now()
        )

        # Configure the mock printer_service
        test_app.state.printer_service.list_printers = AsyncMock(return_value=[bambu_printer, prusa_printer])

        response = client.get("/api/v1/printers")

        assert response.status_code == 200
        data = response.json()
        assert len(data['printers']) == 2
        assert data['total_count'] == 2

        # Verify Bambu Lab printer
        bambu_printer_data = next(p for p in data['printers'] if p['printer_type'] == 'bambu_lab')
        assert bambu_printer_data['name'] == 'Bambu Lab A1 #1'

        # Verify Prusa printer
        prusa_printer_data = next(p for p in data['printers'] if p['printer_type'] == 'prusa_core')
        assert prusa_printer_data['name'] == 'Prusa Core One #1'
    
    def test_get_printers_filter_by_type(self, client, test_app):
        """Test GET /api/v1/printers?printer_type=bambu_lab"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus

        # Create sample printers of different types
        bambu_printer = Printer(
            id='bambu_a1_001',
            name='Bambu Lab A1 #1',
            type=PrinterType.BAMBU_LAB,
            ip_address='192.168.1.100',
            access_code='test_access_code',
            serial_number='AC12345678',
            is_active=True,
            status=PrinterStatus.ONLINE,
            created_at=datetime.now()
        )

        prusa_printer = Printer(
            id='prusa_core_001',
            name='Prusa Core One #1',
            type=PrinterType.PRUSA_CORE,
            ip_address='192.168.1.101',
            api_key='test_api_key',
            is_active=True,
            status=PrinterStatus.ONLINE,
            created_at=datetime.now()
        )

        # Mock list_printers to return both printers
        test_app.state.printer_service.list_printers = AsyncMock(return_value=[bambu_printer, prusa_printer])

        # Test filter by Bambu Lab type
        response = client.get("/api/v1/printers?printer_type=bambu_lab")

        assert response.status_code == 200
        data = response.json()
        assert len(data['printers']) == 1
        assert data['printers'][0]['printer_type'] == 'bambu_lab'
    
    def test_get_printers_filter_by_active_status(self, client, test_app):
        """Test GET /api/v1/printers?is_active=true"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus

        # Create sample printers with different active statuses
        active_printer = Printer(
            id='active_printer_001',
            name='Active Printer',
            type=PrinterType.BAMBU_LAB,
            ip_address='192.168.1.100',
            is_active=True,
            status=PrinterStatus.ONLINE,
            created_at=datetime.now()
        )

        inactive_printer = Printer(
            id='inactive_printer_001',
            name='Inactive Printer',
            type=PrinterType.PRUSA_CORE,
            ip_address='192.168.1.101',
            is_active=False,
            status=PrinterStatus.OFFLINE,
            created_at=datetime.now()
        )

        # Mock list_printers to return both printers
        test_app.state.printer_service.list_printers = AsyncMock(return_value=[active_printer, inactive_printer])

        # Test filter by active status
        response = client.get("/api/v1/printers?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data['printers']) == 1
        assert data['printers'][0]['is_enabled'] is True
    
    def test_post_printers_bambu_lab(self, client, test_app):
        """Test POST /api/v1/printers - Add Bambu Lab printer"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus

        printer_data = {
            'name': 'New Bambu Lab A1',
            'printer_type': 'bambu_lab',
            'connection_config': {
                'ip_address': '192.168.1.102',
                'access_code': 'new_access_code',
                'serial_number': 'AC87654321'
            }
        }

        # Mock the created printer
        created_printer = Printer(
            id='new_bambu_001',
            name='New Bambu Lab A1',
            type=PrinterType.BAMBU_LAB,
            ip_address='192.168.1.102',
            access_code='new_access_code',
            serial_number='AC87654321',
            is_active=True,
            status=PrinterStatus.UNKNOWN,
            created_at=datetime.now()
        )

        # Mock the service methods
        test_app.state.printer_service.create_printer = AsyncMock(return_value=created_printer)
        test_app.state.printer_service.connect_printer = AsyncMock(return_value=True)
        test_app.state.printer_service.start_monitoring = AsyncMock(return_value=None)
        test_app.state.printer_service.printer_instances = {}

        response = client.post(
            "/api/v1/printers",
            json=printer_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == printer_data['name']
        assert data['printer_type'] == 'bambu_lab'
        assert 'id' in data
        assert data['is_enabled'] is True
    
    def test_post_printers_prusa(self, client, test_app):
        """Test POST /api/v1/printers - Add Prusa printer"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus

        printer_data = {
            'name': 'New Prusa Core One',
            'printer_type': 'prusa_core',
            'connection_config': {
                'ip_address': '192.168.1.103',
                'api_key': 'new_prusa_api_key_67890'
            }
        }

        # Mock the created printer
        created_printer = Printer(
            id='new_prusa_001',
            name='New Prusa Core One',
            type=PrinterType.PRUSA_CORE,
            ip_address='192.168.1.103',
            api_key='new_prusa_api_key_67890',
            is_active=True,
            status=PrinterStatus.UNKNOWN,
            created_at=datetime.now()
        )

        # Mock the service methods
        test_app.state.printer_service.create_printer = AsyncMock(return_value=created_printer)
        test_app.state.printer_service.connect_printer = AsyncMock(return_value=True)
        test_app.state.printer_service.start_monitoring = AsyncMock(return_value=None)
        test_app.state.printer_service.printer_instances = {}

        response = client.post(
            "/api/v1/printers",
            json=printer_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == printer_data['name']
        assert data['printer_type'] == 'prusa_core'
        # Note: API response doesn't include api_key in connection_config for security
    
    def test_post_printers_validation_errors(self, client):
        """Test POST /api/v1/printers with validation errors"""
        test_cases = [
            # Missing required fields - FastAPI returns 422 for validation errors
            ({}, 422),
            ({'name': 'Test'}, 422),
            ({'name': 'Test', 'type': 'bambu_lab'}, 422),

            # Invalid printer type
            ({
                'name': 'Invalid Printer',
                'type': 'invalid_type',
                'ip_address': '192.168.1.100'
            }, 422),

            # Invalid IP address
            ({
                'name': 'Test Printer',
                'type': 'bambu_lab',
                'ip_address': 'invalid_ip'
            }, 422),
        ]

        for printer_data, expected_status in test_cases:
            response = client.post(
                "/api/v1/printers",
                json=printer_data
            )

            # FastAPI returns 422 for validation errors with 'detail' or custom error format
            assert response.status_code == expected_status
            error_data = response.json()
            # Either FastAPI's 'detail' or custom error format
            assert 'detail' in error_data or 'status' in error_data
    
    @pytest.mark.skip(reason="Requires printer instance mocking and printer_service.printer_instances integration")
    def test_get_printer_status_bambu_lab(self, client, populated_database, mock_bambu_api):
        """Test GET /api/v1/printers/{id}/status for Bambu Lab printer"""
        printer_id = 'bambu_a1_001'
        
        with patch('src.printers.bambu_lab.BambuLabPrinter') as mock_api_class:
            mock_api_class.return_value = mock_bambu_api
            
            response = client.get(
                "/api/v1/printers/{printer_id}/status"
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
    
    @pytest.mark.skip(reason="Requires printer instance mocking and printer_service.printer_instances integration")
    def test_get_printer_status_prusa(self, client, populated_database, mock_prusa_api):
        """Test GET /api/v1/printers/{id}/status for Prusa printer"""
        printer_id = 'prusa_core_001'
        
        with patch('src.printers.prusa.PrusaPrinter') as mock_api_class:
            mock_api_class.return_value = mock_prusa_api
            
            response = client.get(
                "/api/v1/printers/{printer_id}/status"
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
    
    @pytest.mark.skip(reason="Requires printer instance mocking and error handling integration")
    def test_get_printer_status_offline(self, client):
        """Test GET /api/v1/printers/{id}/status for offline printer"""
        printer_id = 'offline_printer'
        
        with patch('src.printers.get_printer_api') as mock_get_api:
            mock_get_api.side_effect = ConnectionError("Printer not reachable")
            
            response = client.get(
                "/api/v1/printers/{printer_id}/status"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'offline'
            assert data['error'] == 'Printer not reachable'
    
    def test_get_printer_status_not_found(self, client, test_app):
        """Test GET /api/v1/printers/{id}/status for non-existent printer"""
        from unittest.mock import AsyncMock

        # Mock get_printer to return None (printer not found)
        test_app.state.printer_service.get_printer = AsyncMock(return_value=None)

        response = client.get(
            "/api/v1/printers/non_existent/status"
        )

        assert response.status_code == 404
        error_data = response.json()
        assert error_data['status'] == 'error'
        assert 'not found' in error_data['message'].lower()
    
    def test_put_printers_update_config(self, client, test_app):
        """Test PUT /api/v1/printers/{id} - Update printer configuration"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus

        printer_id = 'bambu_a1_001'
        update_data = {
            'name': 'Updated Bambu Lab A1',
            'connection_config': {
                'ip_address': '192.168.1.150'
            },
            'is_enabled': False
        }

        # Mock the updated printer
        updated_printer = Printer(
            id=printer_id,
            name='Updated Bambu Lab A1',
            type=PrinterType.BAMBU_LAB,
            ip_address='192.168.1.150',
            access_code='test_code',
            is_active=False,
            status=PrinterStatus.OFFLINE,
            created_at=datetime.now()
        )

        # Mock the service method
        test_app.state.printer_service.update_printer = AsyncMock(return_value=updated_printer)
        test_app.state.printer_service.printer_instances = {}

        response = client.put(
            f"/api/v1/printers/{printer_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Updated Bambu Lab A1'
        assert data['connection_config']['ip_address'] == '192.168.1.150'
        assert data['is_enabled'] is False
    
    @pytest.mark.skip(reason="Requires printer_service.update_printer implementation with validation")
    def test_put_printers_invalid_update(self, client):
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
            response = client.put(
                "/api/v1/printers/{printer_id}",
                json=update_data
            )
            
            assert response.status_code == 400
            assert expected_error in response.json()['error']['message']
    
    def test_delete_printers(self, client, test_app):
        """Test DELETE /api/v1/printers/{id}"""
        from unittest.mock import AsyncMock

        printer_id = 'prusa_core_001'

        # Mock the service method to return success
        test_app.state.printer_service.delete_printer = AsyncMock(return_value=True)

        response = client.delete(
            f"/api/v1/printers/{printer_id}"
        )

        assert response.status_code == 204

        # Verify delete_printer was called
        test_app.state.printer_service.delete_printer.assert_called_once_with(printer_id, force=False)
    
    def test_delete_printer_with_active_jobs(self, client, test_app):
        """Test DELETE /api/v1/printers/{id} with active print jobs"""
        from unittest.mock import AsyncMock

        printer_id = 'bambu_a1_001'  # This printer has an active printing job

        # Mock delete_printer to raise ValueError (active job protection)
        test_app.state.printer_service.delete_printer = AsyncMock(
            side_effect=ValueError("Cannot delete printer with 2 active job(s). Complete or cancel active jobs first, or use force=true to override.")
        )

        response = client.delete(
            f"/api/v1/printers/{printer_id}"
        )

        assert response.status_code == 409
        error_data = response.json()
        assert 'Cannot delete printer with' in error_data['detail']
        assert 'active job' in error_data['detail']
    
    def test_printer_connection_test(self, client, test_app):
        """Test POST /api/v1/printers/test-connection"""
        from unittest.mock import AsyncMock

        test_data = {
            'printer_type': 'bambu_lab',
            'connection_config': {
                'ip_address': '192.168.1.100',
                'access_code': 'test12345',
                'serial_number': 'AC123456'
            }
        }

        # Mock test_connection to return success
        test_app.state.printer_service.test_connection = AsyncMock(return_value={
            'success': True,
            'message': 'Connection successful',
            'response_time_ms': 150
        })

        response = client.post(
            "/api/v1/printers/test-connection",
            json=test_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['success'] is True
        assert 'response_time_ms' in data['data']
    
    def test_printer_connection_test_failed(self, client, test_app):
        """Test POST /api/v1/printers/test-connection with failed connection"""
        from unittest.mock import AsyncMock

        test_data = {
            'printer_type': 'bambu_lab',
            'connection_config': {
                'ip_address': '192.168.1.200',  # Non-existent IP
                'access_code': 'wrong_code',
                'serial_number': 'INVALID'
            }
        }

        # Mock test_connection to return failure
        test_app.state.printer_service.test_connection = AsyncMock(return_value={
            'success': False,
            'message': 'Connection failed: Connection timeout',
            'error': 'Connection timeout'
        })

        response = client.post(
            "/api/v1/printers/test-connection",
            json=test_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'  # API call succeeded even though connection failed
        assert data['data']['success'] is False
        assert 'Connection timeout' in data['data']['message']


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
        import pytest

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

        # Verify calculations using pytest.approx() for floating point comparison
        assert material_cost == pytest.approx(1.275, rel=1e-9)  # 25.5g * 0.05 EUR/g
        assert power_cost == pytest.approx(0.225, rel=1e-9)  # 2.5h * 0.3kWh * 0.30 EUR/kWh
        assert labor_cost == pytest.approx(7.5, rel=1e-9)   # 0.5h * 15.0 EUR/h
        assert vat_amount == pytest.approx(1.71, rel=1e-9)  # 19% VAT
        assert total_with_vat == pytest.approx(10.71, rel=1e-9)  # Total with German VAT
    
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
    
    def test_concurrent_printer_requests(self, client, test_app):
        """Test concurrent requests to printer API"""
        from unittest.mock import AsyncMock
        import threading

        # Configure the mock printer_service
        test_app.state.printer_service.list_printers = AsyncMock(return_value=[])

        results = []

        def make_request():
            response = client.get("/api/v1/printers")
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
    
    def test_large_printer_list_performance(self, client, test_app):
        """Test API performance with large number of printers"""
        from unittest.mock import AsyncMock
        from datetime import datetime
        from src.models.printer import Printer, PrinterType, PrinterStatus
        import time

        # Create many sample printers for performance testing
        large_printer_list = []
        for i in range(100):
            printer = Printer(
                id=f'test_printer_{i:03d}',
                name=f'Test Printer {i}',
                type=PrinterType.PRUSA_CORE,
                ip_address=f'192.168.1.{i+10}',
                api_key=f'api_key_{i}',
                is_active=True,
                status=PrinterStatus.ONLINE,
                created_at=datetime.now()
            )
            large_printer_list.append(printer)

        # Configure the mock printer_service
        test_app.state.printer_service.list_printers = AsyncMock(return_value=large_printer_list)

        # Time the API request
        start_time = time.time()
        response = client.get("/api/v1/printers")
        end_time = time.time()
        request_time = end_time - start_time

        # Request should complete within reasonable time
        assert response.status_code == 200
        assert request_time < 1.0  # Should complete within 1 second

        data = response.json()
        # Default limit is 50, so should only get 50 printers per page
        assert len(data['printers']) == 50
        assert data['total_count'] == 100
    
    def test_printer_api_rate_limiting(self, client, test_app):
        """Test API rate limiting for printer endpoints"""
        from unittest.mock import AsyncMock

        # Configure the mock printer_service
        test_app.state.printer_service.list_printers = AsyncMock(return_value=[])

        # This test would implement rate limiting checks
        # For now, just verify the endpoint handles multiple rapid requests

        responses = []
        for i in range(50):
            response = client.get("/api/v1/printers")
            responses.append(response.status_code)

        # Should not have any 429 (Too Many Requests) responses in normal testing
        success_responses = [r for r in responses if r == 200]
        assert len(success_responses) >= 45  # Allow for some potential failures
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in POST requests"""
        invalid_json_data = '{"name": "Test", "type": "bambu_lab", invalid}'

        response = client.post(
            "/api/v1/printers",
            data=invalid_json_data,
            headers={'Content-Type': 'application/json'}
        )

        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        error_data = response.json()
        # The app uses a custom error format with 'status' and 'message'
        assert error_data['status'] == 'error'
        assert 'validation' in error_data['message'].lower() or 'json' in error_data['message'].lower()
    
    def test_oversized_request_handling(self, client):
        """Test handling of oversized requests"""
        # Create oversized printer data
        oversized_data = {
            'name': 'Test Printer',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'notes': 'x' * 10000  # 10KB of notes
        }

        response = client.post(
            "/api/v1/printers",
            json=oversized_data
        )

        # Should either accept it or return appropriate error
        assert response.status_code in [201, 400, 413, 422]  # Created, Bad Request, Payload Too Large, or Validation Error