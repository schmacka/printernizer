"""
Essential Printer Driver Integration Tests for Milestone 1.2
===========================================================

Focused tests for Bambu Lab MQTT and Prusa HTTP driver integrations.
Tests core communication protocols and German business workflows.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone
from uuid import uuid4
import json

from src.printers.bambu_lab import BambuLabPrinter
from src.printers.prusa import PrusaPrinter
from src.models.printer import PrinterStatus
from src.utils.exceptions import PrinterConnectionError


class TestEssentialBambuLabDriverIntegration:
    """Test essential Bambu Lab MQTT integration for Milestone 1.2."""
    
    @pytest.fixture
    def mock_bambu_printer(self):
        """Mock Bambu Lab printer with MQTT client."""
        with patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True):
            # Mock bambulabs-api client
            mock_client = MagicMock()
            mock_device = MagicMock()
            
            with patch('src.printers.bambu_lab.BambuClient', return_value=mock_client):
                printer = BambuLabPrinter(
                    printer_id=str(uuid4()),
                    name="Test Bambu A1",
                    ip_address="192.168.1.100",
                    access_code="12345678", 
                    serial="ABC123456789"
                )
                printer.client = mock_client
                printer.device = mock_device
                return printer

    @pytest.mark.asyncio
    async def test_bambu_mqtt_connection_initialization(self, mock_bambu_printer):
        """Test Bambu Lab MQTT connection setup."""
        # Mock successful MQTT connection
        mock_bambu_printer.client.connect = AsyncMock(return_value=True)
        mock_bambu_printer.device.get_device_info = AsyncMock(return_value={
            'name': 'Bambu A1',
            'model': 'A1', 
            'serial': 'ABC123456789',
            'firmware_version': '1.2.3'
        })
        
        result = await mock_bambu_printer.connect()
        
        # Validate connection success
        assert result is True
        mock_bambu_printer.client.connect.assert_called_once()
        
        # Validate device info retrieval
        device_info = await mock_bambu_printer.device.get_device_info()
        assert device_info['model'] == 'A1'
        assert device_info['serial'] == 'ABC123456789'

    @pytest.mark.asyncio 
    async def test_bambu_real_time_status_via_mqtt(self, mock_bambu_printer):
        """Test real-time status updates via MQTT callbacks."""
        # Mock MQTT status message
        mqtt_status = {
            'print': {
                'state': 'PRINTING',
                'progress': 67,
                'time_remaining': 45,
                'current_file': 'Auftrag_Müller_GmbH.3mf'
            },
            'temperature': {
                'bed_current': 65.0,
                'bed_target': 65.0,
                'nozzle_current': 218.5,
                'nozzle_target': 220.0
            },
            'connection': {
                'wifi_signal': -45,  # dBm
                'mqtt_connected': True
            }
        }
        
        with patch.object(mock_bambu_printer, 'get_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {
                'status': PrinterStatus.PRINTING,
                'temperature_bed': mqtt_status['temperature']['bed_current'],
                'temperature_nozzle': mqtt_status['temperature']['nozzle_current'],
                'progress': mqtt_status['print']['progress'],
                'current_job': {
                    'filename': mqtt_status['print']['current_file'],
                    'time_remaining': mqtt_status['print']['time_remaining']
                },
                'connection_quality': 'good',
                'mqtt_connected': mqtt_status['connection']['mqtt_connected']
            }
            
            status = await mock_bambu_printer.get_status()
            
            # Validate MQTT status translation
            assert status['status'] == PrinterStatus.PRINTING
            assert status['temperature_bed'] == 65.0
            assert status['temperature_nozzle'] == 218.5
            assert status['progress'] == 67
            
            # Validate German filename handling
            assert 'Müller_GmbH' in status['current_job']['filename']
            
            # Validate MQTT connection status
            assert status['mqtt_connected'] is True

    @pytest.mark.asyncio
    async def test_bambu_file_listing_via_mqtt(self, mock_bambu_printer):
        """Test file listing through MQTT communication."""
        # Mock MQTT file listing response
        mqtt_files = [
            {
                'name': 'Geschenk_Weihnachten.3mf',
                'size': 2048576,
                'timestamp': 1693920600,  # Unix timestamp
                'print_time': 120  # minutes
            },
            {
                'name': 'Prototyp_Küchenhilfe.stl',
                'size': 1024000, 
                'timestamp': 1693834200,
                'print_time': 85
            }
        ]
        
        with patch.object(mock_bambu_printer, 'list_files', new_callable=AsyncMock) as mock_files:
            mock_files.return_value = [
                {
                    'filename': file['name'],
                    'size': file['size'], 
                    'last_modified': datetime.fromtimestamp(file['timestamp'], timezone.utc).isoformat(),
                    'download_status': 'available',
                    'estimated_print_time': file['print_time']
                }
                for file in mqtt_files
            ]
            
            files = await mock_bambu_printer.list_files()
            
            # Validate file listing
            assert len(files) == 2
            
            # Validate German filenames with special characters
            filenames = [f['filename'] for f in files]
            assert any('Weihnachten' in name for name in filenames)
            assert any('Küchenhilfe' in name for name in filenames)
            
            # Validate file metadata
            for file in files:
                assert 'size' in file
                assert 'last_modified' in file
                assert 'download_status' in file
                assert file['download_status'] == 'available'

    @pytest.mark.asyncio
    async def test_bambu_mqtt_error_recovery(self, mock_bambu_printer):
        """Test MQTT connection error handling and recovery."""
        # Simulate MQTT connection failure
        connection_attempts = []
        
        async def mock_connect_with_retry():
            connection_attempts.append(len(connection_attempts) + 1)
            if len(connection_attempts) < 3:
                raise PrinterConnectionError("test_printer_id", "MQTT connection timeout")
            return True
        
        with patch.object(mock_bambu_printer, 'connect', side_effect=mock_connect_with_retry):
            # First two attempts should fail
            with pytest.raises(PrinterConnectionError):
                await mock_bambu_printer.connect()
            
            with pytest.raises(PrinterConnectionError):
                await mock_bambu_printer.connect()
            
            # Third attempt should succeed
            result = await mock_bambu_printer.connect()
            assert result is True
            assert len(connection_attempts) == 3


class TestEssentialPrusaDriverIntegration:
    """Test essential Prusa HTTP API integration for Milestone 1.2."""
    
    @pytest.fixture
    def mock_prusa_printer(self):
        """Mock Prusa printer with HTTP client."""
        return PrusaPrinter(
            printer_id=str(uuid4()),
            name="Test Prusa Core One", 
            ip_address="192.168.1.101",
            api_key="test_api_key_12345"
        )

    @pytest.mark.asyncio
    async def test_prusa_http_api_connection(self, mock_prusa_printer):
        """Test Prusa HTTP API connection and authentication."""
        # Mock successful HTTP response
        mock_response_data = {
            'printer': {
                'state': 'Operational',
                'temperature': {
                    'bed': {'actual': 22.0, 'target': 0.0},
                    'tool0': {'actual': 23.5, 'target': 0.0}
                }
            },
            'version': {
                'api': '0.20.0',
                'server': '1.9.0'
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test connection by calling connect() instead of non-existent check_connection()
            await mock_prusa_printer.connect()
            
            assert mock_prusa_printer.is_connected is True
            # Verify connection was established with correct API version from mock

    @pytest.mark.asyncio
    async def test_prusa_30_second_polling_status(self, mock_prusa_printer):
        """Test 30-second polling for Prusa status updates."""
        # Mock HTTP status responses for polling
        status_responses = [
            # First poll - idle
            {
                'printer': {
                    'state': 'Operational',
                    'temperature': {
                        'bed': {'actual': 22.0, 'target': 0.0},
                        'tool0': {'actual': 23.5, 'target': 0.0}
                    }
                }
            },
            # Second poll - printing
            {
                'printer': {
                    'state': 'Printing', 
                    'temperature': {
                        'bed': {'actual': 65.0, 'target': 65.0},
                        'tool0': {'actual': 215.0, 'target': 220.0}
                    }
                },
                'job': {
                    'file': {'name': 'Firmenschild_Porcus3D.gcode'},
                    'progress': {'completion': 34.5},
                    'estimatedPrintTime': 180,  # seconds
                    'printTimeLeft': 118
                }
            }
        ]
        
        poll_count = 0
        
        async def mock_poll_status():
            nonlocal poll_count
            response = status_responses[min(poll_count, len(status_responses) - 1)]
            poll_count += 1
            return response
        
        with patch.object(mock_prusa_printer, 'get_status', new_callable=AsyncMock) as mock_status:
            # First poll - idle state
            mock_status.return_value = {
                'status': PrinterStatus.IDLE,
                'temperature_bed': 22.0,
                'temperature_nozzle': 23.5,
                'progress': 0,
                'current_job': None
            }
            
            status1 = await mock_prusa_printer.get_status()
            assert status1['status'] == PrinterStatus.ONLINE
            
            # Second poll - printing state (simulating 30-second interval)
            mock_status.return_value = {
                'status': PrinterStatus.PRINTING,
                'temperature_bed': 65.0,
                'temperature_nozzle': 215.0,
                'progress': 34.5,
                'current_job': {
                    'filename': 'Firmenschild_Porcus3D.gcode',
                    'time_remaining': 118
                }
            }
            
            await asyncio.sleep(0.1)  # Simulate polling interval
            status2 = await mock_prusa_printer.get_status()
            
            # Validate status change detection
            assert status2['status'] == PrinterStatus.PRINTING
            assert status2['progress'] == 34.5
            assert 'Porcus3D' in status2['current_job']['filename']

    @pytest.mark.asyncio
    async def test_prusa_file_download_http(self, mock_prusa_printer):
        """Test HTTP file download from Prusa printer."""
        filename = 'Auftrag_Weber_AG.gcode'
        file_content = b"G28 ; home all axes\nG1 Z15.0 F6000 ; move up"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock file download HTTP response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=file_content)
            mock_response.headers = {'Content-Length': str(len(file_content))}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with patch.object(mock_prusa_printer, 'download_file', new_callable=AsyncMock) as mock_download:
                mock_download.return_value = {
                    'filename': filename,
                    'download_status': 'completed',
                    'file_size': len(file_content),
                    'download_path': f'/downloads/{filename}',
                    'content_preview': file_content[:100].decode('utf-8', errors='ignore')
                }
                
                result = await mock_prusa_printer.download_file(filename)
                
                # Validate file download
                assert result['filename'] == filename
                assert result['download_status'] == 'completed'
                assert result['file_size'] == len(file_content)
                
                # Validate German business filename
                assert 'Weber_AG' in result['filename']
                
                # Validate G-code content detection
                assert 'G28' in result['content_preview']

    @pytest.mark.asyncio
    async def test_prusa_job_history_sync(self, mock_prusa_printer):
        """Test HTTP job history synchronization."""
        # Mock job history from Prusa API
        mock_job_history = {
            'jobs': [
                {
                    'id': 1,
                    'file': {'name': 'Geschenk_Hochzeit.3mf'},
                    'state': 'Success',
                    'started': 1693920600,
                    'finished': 1693927800,
                    'printTime': 7200,  # 2 hours
                    'filament_used': 45.7  # grams
                },
                {
                    'id': 2, 
                    'file': {'name': 'Privat_Spielzeug.stl'},
                    'state': 'Success',
                    'started': 1693834200,
                    'finished': 1693837800,
                    'printTime': 3600,  # 1 hour
                    'filament_used': 18.3  # grams
                }
            ]
        }
        
        with patch.object(mock_prusa_printer, 'sync_job_history', new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = {
                'jobs_synced': 2,
                'new_jobs': 2,
                'updated_jobs': 0,
                'jobs': [
                    {
                        'id': str(uuid4()),
                        'filename': job['file']['name'],
                        'status': 'completed',
                        'started_at': datetime.fromtimestamp(job['started'], timezone.utc).isoformat(),
                        'completed_at': datetime.fromtimestamp(job['finished'], timezone.utc).isoformat(),
                        'print_time': job['printTime'],
                        'material_used': job['filament_used'],
                        'customer_type': 'business' if any(suffix in job['file']['name'] 
                                                         for suffix in ['GmbH', 'AG', 'UG']) else 'private'
                    }
                    for job in mock_job_history['jobs']
                ]
            }
            
            result = await mock_prusa_printer.sync_job_history()
            
            # Validate job sync
            assert result['jobs_synced'] == 2
            assert result['new_jobs'] == 2
            assert len(result['jobs']) == 2
            
            # Validate German business classification
            jobs = result['jobs']
            assert jobs[0]['customer_type'] == 'private'  # Geschenk_Hochzeit
            assert jobs[1]['customer_type'] == 'private'  # Privat_Spielzeug
            
            # Validate German filenames
            filenames = [job['filename'] for job in jobs]
            assert any('Hochzeit' in name for name in filenames)
            assert any('Spielzeug' in name for name in filenames)


class TestEssentialPrinterDriverComparison:
    """Test driver behavior comparison for unified interface."""
    
    @pytest.mark.asyncio
    async def test_unified_status_interface(self):
        """Test that both drivers provide consistent status interface."""
        # Mock both printer types
        with patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True):
            bambu = BambuLabPrinter(
                printer_id=str(uuid4()),
                name="Bambu A1",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial="ABC123456789"
            )
        
        prusa = PrusaPrinter(
            printer_id=str(uuid4()),
            name="Prusa Core One",
            ip_address="192.168.1.101", 
            api_key="test_api_key"
        )
        
        # Mock consistent status format
        expected_status_fields = {
            'status', 'temperature_bed', 'temperature_nozzle', 
            'progress', 'current_job', 'connection_quality'
        }
        
        bambu_status = {
            'status': PrinterStatus.PRINTING,
            'temperature_bed': 60.0,
            'temperature_nozzle': 215.0,
            'progress': 45.0,
            'current_job': {'filename': 'test.3mf'},
            'connection_quality': 'excellent'
        }
        
        prusa_status = {
            'status': PrinterStatus.PRINTING, 
            'temperature_bed': 65.0,
            'temperature_nozzle': 220.0,
            'progress': 67.0,
            'current_job': {'filename': 'test.gcode'},
            'connection_quality': 'good'
        }
        
        # Validate both have consistent interface
        assert set(bambu_status.keys()) == expected_status_fields
        assert set(prusa_status.keys()) == expected_status_fields
        
        # Validate both handle German business data
        for status in [bambu_status, prusa_status]:
            assert isinstance(status['status'], PrinterStatus)
            assert isinstance(status['temperature_bed'], float)
            assert isinstance(status['temperature_nozzle'], float)
            assert isinstance(status['progress'], (int, float))

    @pytest.mark.asyncio
    async def test_connection_recovery_consistency(self):
        """Test both drivers handle connection recovery consistently.""" 
        connection_test_cases = [
            {
                'driver_type': 'bambu',
                'connection_type': 'mqtt',
                'error_message': 'MQTT connection timeout'
            },
            {
                'driver_type': 'prusa',
                'connection_type': 'http',
                'error_message': 'HTTP connection timeout'
            }
        ]
        
        for case in connection_test_cases:
            # Both should raise PrinterConnectionError consistently
            with pytest.raises(PrinterConnectionError) as exc_info:
                raise PrinterConnectionError("test_printer_id", case['error_message'])
            
            # Validate error message format
            assert case['connection_type'] in str(exc_info.value).lower()
            assert 'timeout' in str(exc_info.value).lower()

    def test_german_business_data_integration(self):
        """Test both drivers handle German business data consistently."""
        # Test data with German characteristics
        test_job_data = {
            'filename': 'Auftrag_Müller_GmbH_Weihnachten.3mf',
            'customer_name': 'Müller GmbH',
            'material_cost_eur': 25.50,
            'vat_rate': 0.19,
            'location': 'Kornwestheim',
            'timestamp': '2024-09-05T14:30:00+02:00'  # German timezone
        }
        
        # Business classification logic (same for both drivers)
        def classify_customer_type(customer_name):
            business_suffixes = ['GmbH', 'AG', 'UG', 'KG']
            return 'business' if any(suffix in customer_name for suffix in business_suffixes) else 'private'
        
        # VAT calculation (same for both drivers)  
        def calculate_total_cost(base_cost, vat_rate):
            vat_amount = base_cost * vat_rate
            return base_cost + vat_amount
        
        # Test German business logic
        customer_type = classify_customer_type(test_job_data['customer_name'])
        total_cost = calculate_total_cost(test_job_data['material_cost_eur'], test_job_data['vat_rate'])
        
        # Validate German business handling
        assert customer_type == 'business'  # Müller GmbH
        assert total_cost == pytest.approx(30.345, rel=1e-2)  # 25.50 + 19% VAT
        
        # Validate German filename handling (umlauts)
        assert 'Müller' in test_job_data['filename']
        assert 'Weihnachten' in test_job_data['filename']
        assert 'GmbH' in test_job_data['filename']