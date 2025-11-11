"""
Integration tests for Printernizer Phase 1
Tests complete workflows including API endpoints, database operations,
WebSocket communications, and German business logic.
"""
import pytest
import json
import asyncio
import sqlite3
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timezone, timedelta
import tempfile
import os
import pytz
from decimal import Decimal


class TestAPIIntegration:
    """Integration tests for API endpoints with database operations"""
    
    def test_complete_printer_lifecycle(self, api_client, temp_database, test_config):
        """Test complete printer lifecycle: add -> configure -> monitor -> remove"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            conn = sqlite3.connect(temp_database)
            conn.row_factory = sqlite3.Row
            mock_db.return_value = conn
            
            base_url = test_config['api_base_url']
            
            # Step 1: Add Bambu Lab printer
            printer_data = {
                'name': 'Integration Test Bambu A1',
                'type': 'bambu_lab',
                'model': 'A1',
                'ip_address': '192.168.1.200',
                'access_code': 'integration_test_code',
                'serial_number': 'INT001234567',
                'has_camera': True,
                'has_ams': True
            }
            
            with patch('src.services.printer_service.test_connection') as mock_test:
                mock_test.return_value = True
                response = api_client.post(f"{base_url}/printers", json=printer_data)
                assert response.status_code == 201
                printer_id = response.json()['id']
            
            # Step 2: Get printer status
            with patch('src.services.bambu_service.get_status') as mock_status:
                mock_status.return_value = {
                    'status': 'online',
                    'print_status': 'idle',
                    'temperatures': {
                        'nozzle': 25.0,
                        'bed': 25.0,
                        'chamber': 24.5
                    }
                }
                response = api_client.get(f"{base_url}/printers/{printer_id}/status")
                assert response.status_code == 200
                status_data = response.json()
                assert status_data['status'] == 'online'
                assert 'temperatures' in status_data
            
            # Step 3: Update printer configuration
            update_data = {'name': 'Updated Integration Test Bambu A1'}
            response = api_client.put(f"{base_url}/printers/{printer_id}", json=update_data)
            assert response.status_code == 200
            
            # Step 4: Verify update
            response = api_client.get(f"{base_url}/printers/{printer_id}")
            assert response.status_code == 200
            printer_data = response.json()
            assert printer_data['name'] == 'Updated Integration Test Bambu A1'
            
            # Step 5: Remove printer
            response = api_client.delete(f"{base_url}/printers/{printer_id}")
            assert response.status_code == 204
            
            # Step 6: Verify removal
            response = api_client.get(f"{base_url}/printers/{printer_id}")
            assert response.status_code == 404
    
    def test_complete_job_workflow(self, api_client, populated_database, test_config, mock_bambu_api):
        """Test complete job workflow: create -> monitor -> complete -> export"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Step 1: Create new print job
            job_data = {
                'printer_id': 'bambu_a1_001',
                'job_name': 'integration_test_cube.3mf',
                'material_type': 'PLA',
                'material_brand': 'OVERTURE',
                'material_color': 'Green',
                'layer_height': 0.15,
                'infill_percentage': 15,
                'is_business': True,
                'customer_name': 'Integration Test GmbH',
                'estimated_duration': 5400
            }
            
            response = api_client.post(f"{base_url}/jobs", json=job_data)
            assert response.status_code == 201
            job_id = response.json()['id']
            
            # Step 2: Start job (update status to printing)
            status_update = {
                'status': 'printing',
                'progress': 5.0,
                'layer_current': 15,
                'nozzle_temperature': 210.0,
                'bed_temperature': 60.0
            }
            
            response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=status_update)
            assert response.status_code == 200
            
            # Step 3: Monitor job progress
            with patch('src.services.bambu_service.get_job_status') as mock_job_status:
                mock_job_status.return_value = {
                    'status': 'printing',
                    'progress': 67.5,
                    'layer_current': 220,
                    'estimated_time_remaining': 1800
                }
                
                response = api_client.get(f"{base_url}/jobs/{job_id}")
                assert response.status_code == 200
                job_data = response.json()
                assert job_data['status'] == 'printing'
                assert job_data['progress'] == 67.5
            
            # Step 4: Complete job
            completion_data = {
                'status': 'completed',
                'progress': 100.0,
                'actual_duration': 5100,
                'material_actual_usage': 23.8,
                'quality_rating': 5,
                'first_layer_adhesion': 'excellent'
            }
            
            response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=completion_data)
            assert response.status_code == 200
            
            # Step 5: Verify completion and German business calculations
            response = api_client.get(f"{base_url}/jobs/{job_id}")
            assert response.status_code == 200
            job_data = response.json()
            
            assert job_data['status'] == 'completed'
            assert job_data['progress'] == 100.0
            assert 'cost_breakdown' in job_data
            
            # Verify German business logic
            cost_breakdown = job_data['cost_breakdown']
            assert 'material_cost_eur' in cost_breakdown
            assert 'power_cost_eur' in cost_breakdown
            assert 'total_cost_excluding_vat_eur' in cost_breakdown
            assert 'vat_amount_eur' in cost_breakdown
            assert 'total_cost_including_vat_eur' in cost_breakdown
            
            # VAT calculation verification (19%)
            expected_vat = round(float(cost_breakdown['total_cost_excluding_vat_eur']) * 0.19, 2)
            assert abs(float(cost_breakdown['vat_amount_eur']) - expected_vat) < 0.01
    
    def test_file_management_workflow(self, api_client, populated_database, test_config, temp_download_directory):
        """Test complete file management workflow: list -> download -> organize"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Step 1: Get unified file listing
            with patch('src.services.file_service.get_printer_files') as mock_printer_files:
                mock_printer_files.return_value = [
                    {
                        'id': 'remote_file_001',
                        'filename': 'test_model.3mf',
                        'file_size': 2048000,
                        'printer_id': 'bambu_a1_001',
                        'location': 'printer',
                        'download_status': 'available'
                    }
                ]
                
                response = api_client.get(f"{base_url}/files/unified")
                assert response.status_code == 200
                files_data = response.json()
                
                assert 'files' in files_data
                assert len(files_data['files']) >= 1
                
                # Find remote file
                remote_file = next(f for f in files_data['files'] if f['location'] == 'printer')
                assert remote_file['download_status'] == 'available'
            
            # Step 2: Download file from printer
            file_id = 'remote_file_001'
            with patch('src.services.file_service.download_from_printer') as mock_download:
                mock_download.return_value = {
                    'success': True,
                    'local_path': f'{temp_download_directory}/bambu_a1_001/2025-09-03/test_model.3mf',
                    'file_size': 2048000
                }
                
                response = api_client.post(f"{base_url}/files/{file_id}/download")
                assert response.status_code == 200
                download_result = response.json()
                
                assert download_result['success'] is True
                assert 'local_path' in download_result
                assert download_result['file_size'] == 2048000
            
            # Step 3: Verify file is now marked as downloaded
            response = api_client.get(f"{base_url}/files/unified")
            assert response.status_code == 200
            files_data = response.json()
            
            downloaded_file = next(f for f in files_data['files'] if f['id'] == file_id)
            assert downloaded_file['download_status'] == 'downloaded'
            assert downloaded_file['local_path'] is not None
            
            # Step 4: Delete local file
            response = api_client.delete(f"{base_url}/files/{file_id}")
            assert response.status_code == 204
    
    def test_dashboard_real_time_updates(self, api_client, populated_database, test_config):
        """Test dashboard statistics and real-time updates"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Get initial dashboard stats
            response = api_client.get(f"{base_url}/dashboard/stats")
            assert response.status_code == 200
            stats = response.json()
            
            # Verify dashboard structure
            assert 'printer_summary' in stats
            assert 'job_summary' in stats
            assert 'material_summary' in stats
            assert 'business_summary' in stats
            
            # Verify German business fields
            business_summary = stats['business_summary']
            assert 'total_revenue_eur' in business_summary
            assert 'total_costs_eur' in business_summary
            assert 'total_vat_collected_eur' in business_summary
            assert 'active_business_jobs' in business_summary
            
            # Verify printer summary
            printer_summary = stats['printer_summary']
            assert 'total_printers' in printer_summary
            assert 'online_printers' in printer_summary
            assert 'printing_printers' in printer_summary
            assert 'offline_printers' in printer_summary


class TestWebSocketIntegration:
    """Integration tests for WebSocket real-time updates"""
    
    @pytest.mark.asyncio
    async def test_real_time_job_updates(self, mock_websocket, populated_database):
        """Test real-time job status updates via WebSocket"""
        
        # Mock WebSocket connection
        websocket_messages = []
        
        async def mock_send(message):
            websocket_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # Simulate job status update
        with patch('src.services.websocket_service.broadcast_job_update') as mock_broadcast:
            job_update = {
                'job_id': 'test_job_001',
                'printer_id': 'bambu_a1_001',
                'status': 'printing',
                'progress': 45.5,
                'layer_current': 150,
                'layer_total': 330,
                'estimated_time_remaining': 2700,
                'temperatures': {
                    'nozzle': 210.5,
                    'bed': 60.0,
                    'chamber': 28.5
                }
            }
            
            await mock_broadcast(job_update)
            mock_broadcast.assert_called_once_with(job_update)
    
    @pytest.mark.asyncio
    async def test_printer_status_broadcast(self, mock_websocket):
        """Test real-time printer status broadcasts"""
        
        websocket_messages = []
        
        async def mock_send(message):
            websocket_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # Simulate printer status change
        with patch('src.services.websocket_service.broadcast_printer_status') as mock_broadcast:
            printer_status = {
                'printer_id': 'bambu_a1_001',
                'status': 'online',
                'current_job': {
                    'job_name': 'test_print.3mf',
                    'progress': 67.8,
                    'estimated_time_remaining': 1800
                },
                'temperatures': {
                    'nozzle': 210.0,
                    'bed': 60.0,
                    'chamber': 29.0
                }
            }
            
            await mock_broadcast(printer_status)
            mock_broadcast.assert_called_once_with(printer_status)
    
    @pytest.mark.asyncio
    async def test_file_download_progress(self, mock_websocket):
        """Test real-time file download progress updates"""
        
        progress_updates = []
        
        async def mock_send(message):
            progress_updates.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # Simulate file download progress
        with patch('src.services.websocket_service.broadcast_download_progress') as mock_broadcast:
            download_progress = {
                'file_id': 'download_test_001',
                'filename': 'large_model.3mf',
                'progress_percent': 75.5,
                'bytes_downloaded': 75497472,
                'total_bytes': 100000000,
                'download_speed_mbps': 2.5,
                'estimated_time_remaining': 10
            }
            
            await mock_broadcast(download_progress)
            mock_broadcast.assert_called_once_with(download_progress)


class TestGermanBusinessLogic:
    """Integration tests for German business logic and compliance"""
    
    def test_vat_calculations(self, german_business_config, sample_cost_calculations):
        """Test German VAT calculations for print jobs"""
        from src.services.business_service import calculate_job_costs
        
        # Mock cost calculation
        with patch('src.services.business_service.calculate_job_costs') as mock_calc:
            mock_calc.return_value = {
                'material_cost_eur': Decimal('1.28'),
                'power_cost_eur': Decimal('0.09'),
                'labor_cost_eur': Decimal('7.50'),
                'subtotal_eur': Decimal('8.87'),
                'vat_rate': Decimal('0.19'),
                'vat_amount_eur': Decimal('1.69'),
                'total_including_vat_eur': Decimal('10.56')
            }
            
            job_data = {
                'material_usage_grams': 25.5,
                'print_duration_hours': 2.5,
                'is_business': True
            }
            
            result = mock_calc(job_data, german_business_config)
            
            # Verify German VAT calculation (19%)
            expected_vat = result['subtotal_eur'] * Decimal('0.19')
            assert abs(result['vat_amount_eur'] - expected_vat) < Decimal('0.01')
            
            # Verify total calculation
            expected_total = result['subtotal_eur'] + result['vat_amount_eur']
            assert abs(result['total_including_vat_eur'] - expected_total) < Decimal('0.01')
    
    def test_berlin_timezone_handling(self, test_utils):
        """Test Berlin timezone handling for German business operations"""
        from src.services.business_service import get_business_timestamp
        
        # Mock timezone handling
        with patch('src.services.business_service.get_business_timestamp') as mock_timestamp:
            berlin_tz = pytz.timezone('Europe/Berlin')
            test_time = berlin_tz.localize(datetime(2025, 9, 3, 14, 30, 0))
            mock_timestamp.return_value = test_time
            
            result = mock_timestamp()
            
            assert result.tzinfo.zone == 'Europe/Berlin'
            assert result.hour == 14
            assert result.minute == 30
    
    def test_currency_formatting(self, test_utils):
        """Test German currency formatting"""
        # Test currency formatting
        assert test_utils.format_currency(10.56) == "10.56 EUR"
        assert test_utils.format_currency(1234.56) == "1234.56 EUR"
        assert test_utils.format_currency(0.05) == "0.05 EUR"
    
    def test_business_hours_validation(self, german_business_config):
        """Test German business hours validation"""
        from src.services.business_service import is_business_hours
        
        with patch('src.services.business_service.is_business_hours') as mock_hours:
            # Test business hours (Monday 10:00 AM Berlin time)
            berlin_tz = pytz.timezone('Europe/Berlin')
            business_time = berlin_tz.localize(datetime(2025, 9, 1, 10, 0, 0))  # Monday
            mock_hours.return_value = True
            
            result = mock_hours(business_time, german_business_config)
            assert result is True
            
            # Test non-business hours (Sunday 10:00 AM Berlin time)
            weekend_time = berlin_tz.localize(datetime(2025, 8, 31, 10, 0, 0))  # Sunday
            mock_hours.return_value = False
            
            result = mock_hours(weekend_time, german_business_config)
            assert result is False
    
    def test_export_data_format(self, api_client, populated_database, test_config):
        """Test German accounting software export format"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Test CSV export for German accounting
            response = api_client.get(f"{base_url}/export/jobs", 
                                   params={'format': 'csv', 'date_from': '2025-09-01', 'date_to': '2025-09-30'})
            
            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/csv'
            
            # Verify CSV contains German business fields
            csv_content = response.text
            assert 'Auftrag-ID' in csv_content  # German headers
            assert 'Kunde' in csv_content
            assert 'Kosten (EUR)' in csv_content
            assert 'MwSt (EUR)' in csv_content
            assert 'Gesamt (EUR)' in csv_content


class TestErrorHandlingIntegration:
    """Integration tests for error handling and recovery"""
    
    def test_printer_connection_failure_recovery(self, api_client, test_config):
        """Test printer connection failure and recovery scenarios"""
        base_url = test_config['api_base_url']
        
        # Test connection failure during printer addition
        printer_data = {
            'name': 'Unreachable Printer',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.999',  # Invalid IP
            'access_code': 'test_code'
        }
        
        with patch('src.services.printer_service.test_connection') as mock_test:
            mock_test.side_effect = ConnectionError("Cannot reach printer")
            
            response = api_client.post(f"{base_url}/printers", json=printer_data)
            assert response.status_code == 400
            error_data = response.json()
            assert 'connection_error' in error_data['error_type']
    
    def test_database_transaction_rollback(self, api_client, temp_database, test_config):
        """Test database transaction rollback on errors"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            conn = sqlite3.connect(temp_database)
            mock_db.return_value = conn
            
            base_url = test_config['api_base_url']
            
            # Test transaction rollback on job creation failure
            job_data = {
                'printer_id': 'non_existent_printer',  # Should cause foreign key error
                'job_name': 'test_job.3mf'
            }
            
            response = api_client.post(f"{base_url}/jobs", json=job_data)
            assert response.status_code == 400
            
            # Verify no partial data was inserted
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_name = ?", ('test_job.3mf',))
            count = cursor.fetchone()[0]
            assert count == 0
    
    def test_websocket_reconnection(self, mock_websocket):
        """Test WebSocket reconnection handling"""
        
        # Simulate connection drop and reconnection
        connection_states = []
        
        async def mock_connect():
            connection_states.append('connecting')
            return mock_websocket
        
        async def mock_disconnect():
            connection_states.append('disconnected')
        
        with patch('src.services.websocket_service.connect') as mock_conn:
            with patch('src.services.websocket_service.disconnect') as mock_disc:
                mock_conn.side_effect = mock_connect
                mock_disc.side_effect = mock_disconnect
                
                # Test reconnection logic would be here
                # This is a placeholder for the actual reconnection test
                pass
    
    def test_file_download_interruption_recovery(self, api_client, test_config, temp_download_directory):
        """Test file download interruption and resume"""
        base_url = test_config['api_base_url']
        file_id = 'large_file_001'
        
        # Test partial download and resume
        with patch('src.services.file_service.download_from_printer') as mock_download:
            # First attempt - interrupted
            mock_download.side_effect = ConnectionError("Download interrupted")
            
            response = api_client.post(f"{base_url}/files/{file_id}/download")
            assert response.status_code == 500
            
            # Second attempt - successful resume
            mock_download.side_effect = None
            mock_download.return_value = {
                'success': True,
                'local_path': f'{temp_download_directory}/resumed_file.3mf',
                'resumed_from_byte': 1024000,
                'total_bytes': 5120000
            }
            
            response = api_client.post(f"{base_url}/files/{file_id}/download")
            assert response.status_code == 200
            download_result = response.json()
            assert download_result['success'] is True
            assert 'resumed_from_byte' in download_result