"""
End-to-End tests for Printernizer Phase 1
Tests complete user workflows from start to finish, including:
- Adding printers and setting up monitoring
- Managing print jobs lifecycle
- File downloads and organization
- Dashboard monitoring and reports
- German business workflows

NOTE: These tests require a running server and test endpoints that are not yet implemented.
They are skipped in CI until the features are complete.
"""
import pytest
import asyncio
import sqlite3
import tempfile
import json
import time
from datetime import datetime, timezone
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from contextlib import asynccontextmanager


# Skip reason for tests requiring running server or unimplemented endpoints
SKIP_REASON = "Requires running server and tests unimplemented endpoints (dashboard/stats, files/scan, etc.)"


@pytest.mark.skip(reason=SKIP_REASON)
class TestE2EPrinterSetupWorkflow:
    """End-to-end tests for printer setup workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_bambu_lab_setup(self, api_client, temp_database_with_schema, test_config, mock_bambu_api):
        """Test complete Bambu Lab printer setup workflow"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            conn = sqlite3.connect(temp_database_with_schema)
            conn.row_factory = sqlite3.Row
            mock_db.return_value = conn
            
            base_url = test_config['api_base_url']
            
            # Step 1: Add new Bambu Lab printer
            printer_data = {
                'name': 'E2E Bambu A1',
                'type': 'bambu_lab',
                'model': 'A1',
                'ip_address': '192.168.1.150',
                'access_code': 'e2e_access_code',
                'serial_number': 'E2E001234567',
                'has_camera': True,
                'has_ams': True
            }
            
            with patch('src.services.bambu_service.test_connection') as mock_test:
                mock_test.return_value = True
                with patch('src.services.bambu_service.initialize_monitoring') as mock_monitor:
                    mock_monitor.return_value = True
                    
                    response = api_client.post(f"{base_url}/printers", json=printer_data)
                    assert response.status_code == 201
                    
                    printer_response = response.json()
                    printer_id = printer_response['id']
                    
                    # Verify printer was added to database
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM printers WHERE id = ?", (printer_id,))
                    db_printer = cursor.fetchone()
                    assert db_printer is not None
                    assert db_printer['name'] == 'E2E Bambu A1'
                    assert db_printer['is_active'] is True
            
            # Step 2: Verify printer appears in list
            response = api_client.get(f"{base_url}/printers")
            assert response.status_code == 200
            
            printers_data = response.json()
            assert len(printers_data['printers']) > 0
            
            added_printer = next(p for p in printers_data['printers'] if p['id'] == printer_id)
            assert added_printer['name'] == 'E2E Bambu A1'
            assert added_printer['status'] in ['online', 'connecting']
            
            # Step 3: Check initial status
            with patch('src.services.bambu_service.get_status') as mock_status:
                mock_status.return_value = {
                    'status': 'online',
                    'print_status': 'idle',
                    'temperatures': {
                        'nozzle': 25.0,
                        'bed': 25.0,
                        'chamber': 24.5
                    },
                    'system_info': {
                        'wifi_signal': -45,
                        'firmware_version': '1.04.00.00'
                    }
                }
                
                response = api_client.get(f"{base_url}/printers/{printer_id}/status")
                assert response.status_code == 200
                
                status_data = response.json()
                assert status_data['status'] == 'online'
                assert status_data['print_status'] == 'idle'
                assert 'temperatures' in status_data
            
            # Step 4: Test configuration update
            update_data = {
                'name': 'E2E Bambu A1 Updated',
                'location': 'Workshop A'
            }
            
            response = api_client.put(f"{base_url}/printers/{printer_id}", json=update_data)
            assert response.status_code == 200
            
            # Verify update in database
            cursor.execute("SELECT name, location FROM printers WHERE id = ?", (printer_id,))
            updated_printer = cursor.fetchone()
            assert updated_printer['name'] == 'E2E Bambu A1 Updated'
            assert updated_printer['location'] == 'Workshop A'
    
    @pytest.mark.asyncio
    async def test_complete_prusa_setup(self, api_client, temp_database_with_schema, test_config, mock_prusa_api):
        """Test complete Prusa Core One printer setup workflow"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            conn = sqlite3.connect(temp_database_with_schema)
            conn.row_factory = sqlite3.Row
            mock_db.return_value = conn
            
            base_url = test_config['api_base_url']
            
            # Step 1: Add new Prusa printer
            printer_data = {
                'name': 'E2E Prusa Core One',
                'type': 'prusa',
                'model': 'Core One',
                'ip_address': '192.168.1.151',
                'api_key': 'e2e_prusa_api_key_12345',
                'has_camera': False,
                'supports_remote_control': True
            }
            
            with patch('src.services.prusa_service.test_connection') as mock_test:
                mock_test.return_value = True
                
                response = api_client.post(f"{base_url}/printers", json=printer_data)
                assert response.status_code == 201
                
                printer_id = response.json()['id']
            
            # Step 2: Verify status monitoring
            with patch('src.services.prusa_service.get_status') as mock_status:
                mock_status.return_value = {
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
                        'progress': {'completion': None}
                    }
                }
                
                response = api_client.get(f"{base_url}/printers/{printer_id}/status")
                assert response.status_code == 200
                
                status_data = response.json()
                assert status_data['printer']['state'] == 'Operational'


@pytest.mark.skip(reason=SKIP_REASON)
class TestE2EJobManagementWorkflow:
    """End-to-end tests for complete job management workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_print_job_lifecycle(self, api_client, populated_database, test_config, 
                                               german_business_config, mock_bambu_api):
        """Test complete print job from creation to completion with German business logic"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Step 1: Create business print job
            job_data = {
                'printer_id': 'bambu_a1_001',
                'job_name': 'e2e_business_model.3mf',
                'material_type': 'PLA',
                'material_brand': 'OVERTURE',
                'material_color': 'White',
                'material_estimated_usage': 35.5,
                'material_cost_per_gram': 0.05,
                'layer_height': 0.2,
                'infill_percentage': 20,
                'estimated_duration': 8100,  # 2.25 hours
                'is_business': True,
                'customer_name': 'E2E Test GmbH',
                'customer_email': 'test@e2etest.de'
            }
            
            response = api_client.post(f"{base_url}/jobs", json=job_data)
            assert response.status_code == 201
            
            job_response = response.json()
            job_id = job_response['id']
            assert job_response['status'] == 'queued'
            assert job_response['is_business'] is True
            
            # Step 2: Start printing (status transition)
            start_status = {
                'status': 'printing',
                'progress': 0.0,
                'layer_current': 1,
                'nozzle_temperature': 210.0,
                'bed_temperature': 60.0,
                'started_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=start_status)
            assert response.status_code == 200
            
            # Step 3: Simulate progress updates
            progress_updates = [
                {'progress': 25.0, 'layer_current': 85, 'estimated_time_remaining': 6075},
                {'progress': 50.0, 'layer_current': 170, 'estimated_time_remaining': 4050},
                {'progress': 75.0, 'layer_current': 255, 'estimated_time_remaining': 2025}
            ]
            
            for update in progress_updates:
                response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=update)
                assert response.status_code == 200
                
                # Verify progress in database
                cursor = populated_database.cursor()
                cursor.execute("SELECT progress FROM jobs WHERE id = ?", (job_id,))
                db_progress = cursor.fetchone()[0]
                assert abs(db_progress - update['progress']) < 0.1
            
            # Step 4: Complete job with German business calculations
            completion_data = {
                'status': 'completed',
                'progress': 100.0,
                'actual_duration': 7650,  # 2.125 hours
                'material_actual_usage': 34.2,
                'power_consumption_kwh': 0.64,  # 2.125h * 0.3kW
                'quality_rating': 5,
                'first_layer_adhesion': 'excellent',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            
            with patch('src.services.business_service.calculate_job_costs') as mock_calc:
                # Mock German business cost calculation
                mock_calc.return_value = {
                    'material_cost_eur': 1.71,  # 34.2g * 0.05
                    'power_cost_eur': 0.19,     # 0.64 kWh * 0.30
                    'labor_cost_eur': 10.63,    # 2.125h * 0.5 * 10.0 (labor factor)
                    'subtotal_eur': 12.53,
                    'vat_rate': 0.19,
                    'vat_amount_eur': 2.38,
                    'total_including_vat_eur': 14.91
                }
                
                response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=completion_data)
                assert response.status_code == 200
            
            # Step 5: Verify final job details with German business data
            response = api_client.get(f"{base_url}/jobs/{job_id}")
            assert response.status_code == 200
            
            final_job = response.json()
            assert final_job['status'] == 'completed'
            assert final_job['progress'] == 100.0
            assert final_job['is_business'] is True
            
            # Verify German business calculations
            cost_breakdown = final_job['cost_breakdown']
            assert 'material_cost_eur' in cost_breakdown
            assert 'vat_amount_eur' in cost_breakdown
            assert 'total_including_vat_eur' in cost_breakdown
            
            # VAT should be 19% of subtotal
            vat_rate = cost_breakdown['vat_amount_eur'] / cost_breakdown['subtotal_eur']
            assert abs(vat_rate - 0.19) < 0.01
            
            # Step 6: Verify job appears in completed jobs list
            response = api_client.get(f"{base_url}/jobs?status=completed&is_business=true")
            assert response.status_code == 200
            
            completed_jobs = response.json()
            completed_job = next(job for job in completed_jobs['jobs'] if job['id'] == job_id)
            assert completed_job['customer_name'] == 'E2E Test GmbH'
    
    @pytest.mark.asyncio
    async def test_job_failure_and_recovery(self, api_client, populated_database, test_config):
        """Test job failure scenarios and recovery workflow"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Create job
            job_data = {
                'printer_id': 'bambu_a1_001',
                'job_name': 'failure_test_model.3mf',
                'material_type': 'PLA',
                'estimated_duration': 3600,
                'is_business': False
            }
            
            response = api_client.post(f"{base_url}/jobs", json=job_data)
            job_id = response.json()['id']
            
            # Start job
            response = api_client.put(f"{base_url}/jobs/{job_id}/status", 
                                    json={'status': 'printing', 'progress': 0.0})
            assert response.status_code == 200
            
            # Simulate failure at 30% progress
            failure_data = {
                'status': 'failed',
                'progress': 30.0,
                'failure_reason': 'Nozzle clog detected',
                'failure_category': 'mechanical',
                'failed_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=failure_data)
            assert response.status_code == 200
            
            # Verify failure recorded
            response = api_client.get(f"{base_url}/jobs/{job_id}")
            failed_job = response.json()
            assert failed_job['status'] == 'failed'
            assert failed_job['failure_reason'] == 'Nozzle clog detected'
            
            # Test job restart
            restart_data = {
                'status': 'printing',
                'progress': 0.0,
                'restarted_from_failed': True,
                'restart_reason': 'Nozzle cleaned, retrying print'
            }
            
            response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=restart_data)
            assert response.status_code == 200
            
            # Verify restart
            response = api_client.get(f"{base_url}/jobs/{job_id}")
            restarted_job = response.json()
            assert restarted_job['status'] == 'printing'
            assert restarted_job['progress'] == 0.0


@pytest.mark.skip(reason=SKIP_REASON)
class TestE2EFileManagementWorkflow:
    """End-to-end tests for file management workflow (Drucker-Dateien system)"""
    
    @pytest.mark.asyncio
    async def test_complete_file_download_workflow(self, api_client, populated_database, 
                                                 test_config, temp_download_directory):
        """Test complete file discovery, download, and organization workflow"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Step 1: Discover files on printers
            with patch('src.services.file_service.scan_printer_files') as mock_scan:
                mock_scan.return_value = {
                    'bambu_a1_001': [
                        {
                            'filename': 'discovered_model_1.3mf',
                            'file_size': 3145728,
                            'printer_path': '/storage/discovered_model_1.3mf',
                            'last_modified': '2025-09-03T12:00:00Z',
                            'file_type': '.3mf'
                        },
                        {
                            'filename': 'discovered_model_2.stl',
                            'file_size': 5242880,
                            'printer_path': '/storage/discovered_model_2.stl',
                            'last_modified': '2025-09-03T11:30:00Z',
                            'file_type': '.stl'
                        }
                    ]
                }
                
                # Trigger file scan
                response = api_client.post(f"{base_url}/files/scan")
                assert response.status_code == 200
                
                scan_result = response.json()
                assert scan_result['files_discovered'] >= 2
            
            # Step 2: Get unified file listing
            response = api_client.get(f"{base_url}/files/unified")
            assert response.status_code == 200
            
            files_data = response.json()
            assert len(files_data['files']) >= 2
            
            # Find available files for download
            available_files = [f for f in files_data['files'] 
                             if f['download_status'] == 'available' and f['location'] == 'printer']
            assert len(available_files) >= 2
            
            # Step 3: Download first file
            file_to_download = available_files[0]
            
            with patch('src.services.file_service.download_from_printer') as mock_download:
                mock_download.return_value = {
                    'success': True,
                    'local_path': f'{temp_download_directory}/bambu_a1_001/2025-09-03/{file_to_download["filename"]}',
                    'file_size': file_to_download['file_size'],
                    'download_time_seconds': 15.5,
                    'download_speed_mbps': 1.6
                }
                
                response = api_client.post(f"{base_url}/files/{file_to_download['id']}/download")
                assert response.status_code == 200
                
                download_result = response.json()
                assert download_result['success'] is True
                assert 'local_path' in download_result
            
            # Step 4: Verify file status updated
            response = api_client.get(f"{base_url}/files/unified")
            files_data = response.json()
            
            downloaded_file = next(f for f in files_data['files'] if f['id'] == file_to_download['id'])
            assert downloaded_file['download_status'] == 'downloaded'
            assert downloaded_file['local_path'] is not None
            
            # Step 5: Test batch download
            remaining_files = [f['id'] for f in available_files[1:3]]  # Download next 2 files
            
            batch_download_data = {
                'file_ids': remaining_files,
                'organize_by': 'printer_date'  # Organize by printer and date
            }
            
            with patch('src.services.file_service.batch_download') as mock_batch:
                mock_batch.return_value = {
                    'success': True,
                    'downloaded_files': len(remaining_files),
                    'failed_files': 0,
                    'total_size_mb': 8.0,
                    'total_time_seconds': 45.2
                }
                
                response = api_client.post(f"{base_url}/files/batch-download", json=batch_download_data)
                assert response.status_code == 200
                
                batch_result = response.json()
                assert batch_result['success'] is True
                assert batch_result['downloaded_files'] == len(remaining_files)
            
            # Step 6: Verify file organization
            response = api_client.get(f"{base_url}/files/unified?location=local")
            local_files = response.json()
            
            # Should have organized files by printer and date
            local_file_paths = [f['local_path'] for f in local_files['files'] if f['local_path']]
            
            for path in local_file_paths:
                assert 'bambu_a1_001' in path  # Printer-based organization
                assert '2025-09-03' in path     # Date-based organization
    
    @pytest.mark.asyncio
    async def test_file_cleanup_workflow(self, api_client, populated_database, test_config):
        """Test file cleanup and management workflow"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Create some downloaded files for cleanup
            test_files = [
                {'id': 'cleanup_001', 'age_days': 30, 'size_mb': 50},
                {'id': 'cleanup_002', 'age_days': 60, 'size_mb': 100},
                {'id': 'cleanup_003', 'age_days': 90, 'size_mb': 25}
            ]
            
            # Step 1: Get cleanup recommendations
            response = api_client.get(f"{base_url}/files/cleanup-recommendations")
            assert response.status_code == 200
            
            cleanup_data = response.json()
            assert 'recommendations' in cleanup_data
            assert 'total_space_recoverable_mb' in cleanup_data
            
            # Step 2: Execute selective cleanup (files older than 45 days)
            cleanup_request = {
                'max_age_days': 45,
                'min_size_mb': 30,
                'preserve_recent_business_files': True
            }
            
            with patch('src.services.file_service.cleanup_files') as mock_cleanup:
                mock_cleanup.return_value = {
                    'files_deleted': 1,
                    'space_recovered_mb': 100.0,
                    'cleanup_summary': {
                        'old_files_deleted': 1,
                        'large_files_deleted': 0,
                        'business_files_preserved': 5
                    }
                }
                
                response = api_client.post(f"{base_url}/files/cleanup", json=cleanup_request)
                assert response.status_code == 200
                
                cleanup_result = response.json()
                assert cleanup_result['files_deleted'] > 0
                assert cleanup_result['space_recovered_mb'] > 0


@pytest.mark.skip(reason=SKIP_REASON)
class TestE2EDashboardWorkflow:
    """End-to-end tests for dashboard monitoring and reporting"""
    
    @pytest.mark.asyncio
    async def test_complete_dashboard_monitoring(self, api_client, populated_database, test_config, 
                                               german_business_config):
        """Test complete dashboard monitoring with German business reporting"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Step 1: Get initial dashboard statistics
            response = api_client.get(f"{base_url}/dashboard/stats")
            assert response.status_code == 200
            
            initial_stats = response.json()
            
            # Verify German business fields
            assert 'business_summary' in initial_stats
            business_summary = initial_stats['business_summary']
            
            assert 'total_revenue_eur' in business_summary
            assert 'total_costs_eur' in business_summary
            assert 'total_vat_collected_eur' in business_summary
            assert 'profit_margin_percent' in business_summary
            
            # Step 2: Generate monthly business report
            report_request = {
                'period': 'monthly',
                'year': 2025,
                'month': 9,
                'include_vat_breakdown': True,
                'include_material_usage': True,
                'format': 'detailed'
            }
            
            with patch('src.services.reporting_service.generate_business_report') as mock_report:
                mock_report.return_value = {
                    'report_period': 'September 2025',
                    'summary': {
                        'total_jobs': 15,
                        'business_jobs': 8,
                        'private_jobs': 7,
                        'total_revenue_eur': 456.78,
                        'total_costs_eur': 234.56,
                        'net_profit_eur': 222.22,
                        'vat_collected_eur': 86.79
                    },
                    'material_usage': {
                        'total_filament_kg': 2.5,
                        'pla_usage_percent': 60,
                        'petg_usage_percent': 25,
                        'tpu_usage_percent': 15
                    },
                    'german_tax_data': {
                        'vat_rate': 0.19,
                        'total_net_revenue_eur': 383.99,
                        'total_vat_eur': 86.79,
                        'deductible_costs_eur': 234.56
                    }
                }
                
                response = api_client.post(f"{base_url}/reports/business", json=report_request)
                assert response.status_code == 200
                
                report = response.json()
                assert report['summary']['total_jobs'] == 15
                assert report['german_tax_data']['vat_rate'] == 0.19
                
                # Verify VAT calculation
                expected_vat = round(report['summary']['total_revenue_eur'] / 1.19 * 0.19, 2)
                assert abs(report['german_tax_data']['total_vat_eur'] - expected_vat) < 1.0
            
            # Step 3: Export data for German accounting software
            export_request = {
                'format': 'csv',
                'date_from': '2025-09-01',
                'date_to': '2025-09-30',
                'include_vat_breakdown': True,
                'german_format': True
            }
            
            response = api_client.post(f"{base_url}/export/accounting", json=export_request)
            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/csv'
            
            # Verify CSV contains German fields
            csv_content = response.text
            german_headers = ['Auftrag-ID', 'Kunde', 'Kosten (EUR)', 'MwSt (EUR)', 'Gesamt (EUR)']
            for header in german_headers:
                assert header in csv_content
    
    @pytest.mark.asyncio
    async def test_real_time_dashboard_updates(self, api_client, populated_database, test_config, mock_websocket):
        """Test real-time dashboard updates via WebSocket"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            base_url = test_config['api_base_url']
            
            # Step 1: Establish WebSocket connection
            ws_url = test_config['websocket_url']
            
            # Mock WebSocket connection and message handling
            received_messages = []
            
            async def mock_websocket_handler():
                # Simulate dashboard subscription
                subscription_message = {
                    'type': 'subscribe',
                    'data': {
                        'channels': ['printer_status', 'job_progress', 'dashboard_stats']
                    }
                }
                
                # Mock sending subscription
                await mock_websocket.send(json.dumps(subscription_message))
                
                # Simulate receiving real-time updates
                updates = [
                    {
                        'type': 'printer_status',
                        'data': {
                            'printer_id': 'bambu_a1_001',
                            'status': 'printing',
                            'current_job': {
                                'job_id': 'test_job_001',
                                'progress': 45.5
                            }
                        }
                    },
                    {
                        'type': 'job_progress',
                        'data': {
                            'job_id': 'test_job_001',
                            'progress': 50.0,
                            'estimated_time_remaining': 3600
                        }
                    },
                    {
                        'type': 'dashboard_stats',
                        'data': {
                            'active_jobs': 3,
                            'online_printers': 1,
                            'current_revenue_eur': 1250.50
                        }
                    }
                ]
                
                for update in updates:
                    received_messages.append(update)
                    await asyncio.sleep(0.1)  # Simulate real-time intervals
            
            # Execute WebSocket simulation
            await mock_websocket_handler()
            
            # Verify messages received
            assert len(received_messages) == 3
            assert received_messages[0]['type'] == 'printer_status'
            assert received_messages[1]['type'] == 'job_progress'
            assert received_messages[2]['type'] == 'dashboard_stats'
            
            # Verify dashboard would update with real-time data
            dashboard_update = received_messages[2]['data']
            assert dashboard_update['active_jobs'] == 3
            assert dashboard_update['current_revenue_eur'] == 1250.50


@pytest.mark.skip(reason=SKIP_REASON)
class TestE2EGermanBusinessCompliance:
    """End-to-end tests for German business compliance and tax reporting"""
    
    @pytest.mark.asyncio
    async def test_complete_vat_compliance_workflow(self, api_client, temp_database_with_schema, test_config,
                                                  german_business_config):
        """Test complete German VAT compliance workflow"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            conn = sqlite3.connect(temp_database_with_schema)
            conn.row_factory = sqlite3.Row
            mock_db.return_value = conn
            
            # Initialize database with German business settings
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value, category) VALUES 
                ('vat_rate', '0.19', 'business'),
                ('currency', 'EUR', 'business'),
                ('timezone', 'Europe/Berlin', 'business'),
                ('business_registration', 'DE123456789', 'business')
            """)
            conn.commit()
            
            base_url = test_config['api_base_url']
            
            # Step 1: Create business jobs with VAT calculations
            business_jobs = [
                {
                    'printer_id': 'bambu_a1_001',
                    'job_name': 'vat_test_1.3mf',
                    'material_cost_eur': 5.00,
                    'labor_cost_eur': 15.00,
                    'is_business': True,
                    'customer_name': 'VAT Test GmbH',
                    'customer_vat_id': 'DE987654321'
                },
                {
                    'printer_id': 'bambu_a1_001', 
                    'job_name': 'vat_test_2.3mf',
                    'material_cost_eur': 8.50,
                    'labor_cost_eur': 25.00,
                    'is_business': True,
                    'customer_name': 'VAT Test AG',
                    'customer_vat_id': 'DE555666777'
                }
            ]
            
            job_ids = []
            for job_data in business_jobs:
                response = api_client.post(f"{base_url}/jobs", json=job_data)
                assert response.status_code == 201
                job_ids.append(response.json()['id'])
            
            # Step 2: Complete jobs and calculate VAT
            for i, job_id in enumerate(job_ids):
                completion_data = {
                    'status': 'completed',
                    'progress': 100.0,
                    'material_cost_eur': business_jobs[i]['material_cost_eur'],
                    'labor_cost_eur': business_jobs[i]['labor_cost_eur']
                }
                
                with patch('src.services.business_service.calculate_vat') as mock_vat:
                    subtotal = completion_data['material_cost_eur'] + completion_data['labor_cost_eur']
                    vat_amount = round(subtotal * 0.19, 2)
                    total_with_vat = subtotal + vat_amount
                    
                    mock_vat.return_value = {
                        'subtotal_eur': subtotal,
                        'vat_rate': 0.19,
                        'vat_amount_eur': vat_amount,
                        'total_including_vat_eur': total_with_vat
                    }
                    
                    response = api_client.put(f"{base_url}/jobs/{job_id}/status", json=completion_data)
                    assert response.status_code == 200
            
            # Step 3: Generate VAT report
            vat_report_request = {
                'period': 'monthly',
                'year': 2025,
                'month': 9,
                'report_type': 'vat_summary'
            }
            
            with patch('src.services.tax_service.generate_vat_report') as mock_vat_report:
                mock_vat_report.return_value = {
                    'period': 'September 2025',
                    'total_net_sales_eur': 53.50,  # 20.00 + 33.50
                    'total_vat_collected_eur': 10.17,  # 19% of total
                    'vat_rate': 0.19,
                    'business_registration': 'DE123456789',
                    'transactions': [
                        {
                            'customer_vat_id': 'DE987654321',
                            'net_amount_eur': 20.00,
                            'vat_amount_eur': 3.80,
                            'total_eur': 23.80
                        },
                        {
                            'customer_vat_id': 'DE555666777',
                            'net_amount_eur': 33.50,
                            'vat_amount_eur': 6.37,
                            'total_eur': 39.87
                        }
                    ]
                }
                
                response = api_client.post(f"{base_url}/reports/vat", json=vat_report_request)
                assert response.status_code == 200
                
                vat_report = response.json()
                assert vat_report['vat_rate'] == 0.19
                assert vat_report['business_registration'] == 'DE123456789'
                assert len(vat_report['transactions']) == 2
                
                # Verify VAT calculations
                total_vat = sum(t['vat_amount_eur'] for t in vat_report['transactions'])
                assert abs(total_vat - vat_report['total_vat_collected_eur']) < 0.01
            
            # Step 4: Export for German tax software (ELSTER format)
            elster_export_request = {
                'format': 'elster_xml',
                'period': '2025-09',
                'company_details': {
                    'name': 'Porcus3D',
                    'vat_id': 'DE123456789',
                    'address': 'Kornwestheim, Germany'
                }
            }
            
            response = api_client.post(f"{base_url}/export/elster", json=elster_export_request)
            assert response.status_code == 200
            assert response.headers['content-type'] == 'application/xml'
            
            # Verify XML contains required ELSTER elements
            xml_content = response.text
            assert 'USt-VA' in xml_content  # German VAT return format
            assert 'DE123456789' in xml_content  # VAT ID
            assert '10.17' in xml_content  # Total VAT amount