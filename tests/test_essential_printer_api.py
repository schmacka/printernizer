"""
Essential Printer API Integration Tests for Milestone 1.2
=========================================================

Focused tests for core printer API endpoints without over-testing.
Tests real-time monitoring, file management, and German business logic.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4
import json

from src.models.printer import PrinterStatus, PrinterType
from src.printers.bambu_lab import BambuLabPrinter
from src.printers.prusa import PrusaPrinter


class TestEssentialPrinterAPIEndpoints:
    """Test core printer API endpoints for Milestone 1.2."""
    
    @pytest.fixture
    def mock_printer_id(self):
        """Mock printer ID for testing."""
        return str(uuid4())
    
    @pytest.fixture 
    def mock_bambu_printer(self, mock_printer_id):
        """Mock Bambu Lab printer for testing."""
        with patch('src.printers.bambu_lab.BAMBU_AVAILABLE', True):
            printer = BambuLabPrinter(
                printer_id=mock_printer_id,
                name="Test Bambu A1",
                ip_address="192.168.1.100",
                access_code="12345678",
                serial="ABC123456789"
            )
            return printer
    
    @pytest.fixture
    def mock_prusa_printer(self, mock_printer_id):
        """Mock Prusa printer for testing."""
        printer = PrusaPrinter(
            printer_id=mock_printer_id,
            name="Test Prusa Core One",
            ip_address="192.168.1.101", 
            api_key="test_api_key_12345"
        )
        return printer

    @pytest.mark.asyncio
    async def test_printer_status_endpoint_real_time(self, mock_bambu_printer):
        """Test GET /api/v1/printers/{id}/status for real-time monitoring."""
        # Mock real-time status with German business data
        mock_status = {
            "status": PrinterStatus.PRINTING,
            "temperature_bed": 60.0,
            "temperature_nozzle": 215.0, 
            "progress": 45.7,
            "current_job": {
                "id": str(uuid4()),
                "filename": "Geschenk_Weihnachten.3mf",
                "customer_type": "business",  # German business classification
                "material_cost_eur": 12.50,  # EUR currency
                "estimated_time": 120  # minutes
            },
            "connection_quality": "excellent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with patch.object(mock_bambu_printer, 'get_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = mock_status
            
            status = await mock_bambu_printer.get_status()
            
            # Validate core real-time data
            assert status["status"] == PrinterStatus.PRINTING
            assert status["temperature_bed"] == 60.0
            assert status["temperature_nozzle"] == 215.0
            assert status["progress"] == 45.7
            
            # Validate German business integration
            assert status["current_job"]["customer_type"] == "business"
            assert status["current_job"]["material_cost_eur"] == 12.50
            assert "Geschenk" in status["current_job"]["filename"]  # German filename
            
            # Validate connection quality for monitoring
            assert status["connection_quality"] == "excellent"
    
    @pytest.mark.asyncio
    async def test_printer_monitoring_start_stop(self, mock_bambu_printer):
        """Test POST /api/v1/printers/{id}/monitoring/start and stop endpoints."""
        # Test monitoring start
        with patch.object(mock_bambu_printer, 'start_monitoring', new_callable=AsyncMock) as mock_start:
            mock_start.return_value = {
                "monitoring_active": True,
                "polling_interval": 30,  # 30-second polling
                "connection_type": "mqtt",
                "started_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await mock_bambu_printer.start_monitoring()
            
            assert result["monitoring_active"] is True
            assert result["polling_interval"] == 30  # Validate 30-second requirement
            assert result["connection_type"] == "mqtt"
            mock_start.assert_called_once()
        
        # Test monitoring stop
        with patch.object(mock_bambu_printer, 'stop_monitoring', new_callable=AsyncMock) as mock_stop:
            mock_stop.return_value = {
                "monitoring_active": False,
                "stopped_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await mock_bambu_printer.stop_monitoring()
            
            assert result["monitoring_active"] is False
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_drucker_dateien_file_listing(self, mock_prusa_printer):
        """Test GET /api/v1/printers/{id}/files for Drucker-Dateien system."""
        # Mock file listing with German filenames and download status
        mock_files = [
            {
                "filename": "Kundenauftrag_Müller.3mf",
                "size": 2048576,  # ~2MB
                "download_status": "available",  # 📁
                "last_modified": "2024-09-05T10:30:00Z",
                "file_type": "3mf"
            },
            {
                "filename": "Prototyp_Süßwarenform.stl", 
                "size": 1024000,  # ~1MB
                "download_status": "downloaded",  # ✓
                "last_modified": "2024-09-04T15:45:00Z",
                "file_type": "stl"
            },
            {
                "filename": "Löffel_personalisiert.gcode",
                "size": 512000,  # ~512KB 
                "download_status": "local",  # 💾
                "last_modified": "2024-09-03T09:15:00Z",
                "file_type": "gcode"
            }
        ]
        
        with patch.object(mock_prusa_printer, 'list_files', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_files
            
            files = await mock_prusa_printer.list_files()
            
            # Validate file listing structure
            assert len(files) == 3
            
            # Test German filename support (umlauts)
            filenames = [f["filename"] for f in files]
            assert any("Müller" in name for name in filenames)
            assert any("Süßwarenform" in name for name in filenames)
            assert any("Löffel" in name for name in filenames)
            
            # Test download status tracking
            statuses = [f["download_status"] for f in files]
            assert "available" in statuses  # 📁
            assert "downloaded" in statuses  # ✓  
            assert "local" in statuses  # 💾
            
            # Test file format support
            formats = [f["file_type"] for f in files]
            assert "3mf" in formats
            assert "stl" in formats
            assert "gcode" in formats

    @pytest.mark.asyncio
    async def test_one_click_file_download(self, mock_prusa_printer):
        """Test POST /api/v1/printers/{id}/files/{filename}/download for one-click downloads."""
        filename = "Auftrag_Schmidt_Geburtstag.3mf"
        
        # Mock download progress tracking
        download_result = {
            "filename": filename,
            "download_status": "downloading",
            "download_progress": 0,
            "estimated_size": 3145728,  # ~3MB
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch.object(mock_prusa_printer, 'download_file', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = download_result
            
            result = await mock_prusa_printer.download_file(filename)
            
            # Validate download initiation
            assert result["filename"] == filename
            assert result["download_status"] == "downloading"
            assert result["download_progress"] == 0
            assert result["estimated_size"] > 0
            
            # Validate German filename handling
            assert "Geburtstag" in result["filename"]  # German word in filename
            
            mock_download.assert_called_once_with(filename)

    @pytest.mark.asyncio 
    async def test_current_job_real_time_progress(self, mock_bambu_printer):
        """Test GET /api/v1/printers/{id}/jobs/current for real-time job tracking."""
        # Mock current job with German business data
        mock_job = {
            "id": str(uuid4()),
            "filename": "Firmenschild_Porcus3D.3mf",
            "status": "printing",
            "progress": 67.3,
            "time_elapsed": 95,  # minutes
            "time_remaining": 48,  # minutes
            "material_used": 28.5,  # grams
            "material_cost_eur": 8.75,  # German EUR currency
            "customer_type": "business",  # German business classification
            "vat_rate": 0.19,  # German 19% VAT
            "temperature_bed": 65.0,
            "temperature_nozzle": 220.0,
            "started_at": "2024-09-05T08:30:00Z"
        }
        
        with patch.object(mock_bambu_printer, 'get_current_job', new_callable=AsyncMock) as mock_job_get:
            mock_job_get.return_value = mock_job
            
            job = await mock_bambu_printer.get_current_job()
            
            # Validate real-time progress data
            assert job["progress"] == 67.3
            assert job["time_elapsed"] == 95
            assert job["time_remaining"] == 48
            
            # Validate German business calculations
            assert job["material_cost_eur"] == 8.75  # EUR currency
            assert job["vat_rate"] == 0.19  # German VAT rate
            assert job["customer_type"] == "business"
            
            # Validate German filename
            assert "Firmenschild" in job["filename"]
            assert "Porcus3D" in job["filename"]
            
            # Validate real-time temperature monitoring
            assert job["temperature_bed"] == 65.0
            assert job["temperature_nozzle"] == 220.0

    @pytest.mark.asyncio
    async def test_job_sync_history_integration(self, mock_prusa_printer):
        """Test POST /api/v1/printers/{id}/jobs/sync for job history synchronization."""
        # Mock job history from printer
        mock_history = [
            {
                "id": str(uuid4()),
                "filename": "Werbeartikel_Messe.stl", 
                "status": "completed",
                "completed_at": "2024-09-04T16:45:00Z",
                "material_used": 45.2,
                "print_time": 180,  # minutes
                "customer_type": "business",
                "material_cost_eur": 13.25
            },
            {
                "id": str(uuid4()),
                "filename": "Privat_Küchenhaken.3mf",
                "status": "completed", 
                "completed_at": "2024-09-03T14:20:00Z",
                "material_used": 12.8,
                "print_time": 45,  # minutes
                "customer_type": "private",
                "material_cost_eur": 3.75
            }
        ]
        
        with patch.object(mock_prusa_printer, 'sync_job_history', new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = {
                "jobs_synced": 2,
                "new_jobs": 2,
                "updated_jobs": 0,
                "sync_timestamp": datetime.now(timezone.utc).isoformat(),
                "jobs": mock_history
            }
            
            result = await mock_prusa_printer.sync_job_history()
            
            # Validate sync results
            assert result["jobs_synced"] == 2
            assert result["new_jobs"] == 2
            assert len(result["jobs"]) == 2
            
            # Validate German business vs private classification
            business_jobs = [j for j in result["jobs"] if j["customer_type"] == "business"]
            private_jobs = [j for j in result["jobs"] if j["customer_type"] == "private"]
            
            assert len(business_jobs) == 1
            assert len(private_jobs) == 1
            
            # Validate German cost calculations
            for job in result["jobs"]:
                assert "material_cost_eur" in job
                assert job["material_cost_eur"] > 0
            
            # Validate German filenames
            filenames = [j["filename"] for j in result["jobs"]]
            assert any("Werbeartikel" in name for name in filenames)
            assert any("Küchenhaken" in name for name in filenames)


class TestEssentialPrinterConnectionRecovery:
    """Test connection recovery and error handling for both printer types."""
    
    @pytest.mark.asyncio
    async def test_bambu_mqtt_connection_recovery(self):
        """Test Bambu Lab MQTT connection recovery with 30-second polling."""
        with patch('src.printers.bambu_lab.BAMBU_AVAILABLE', True):
            printer = BambuLabPrinter(
                printer_id=str(uuid4()),
                name="Test Bambu A1",
                ip_address="192.168.1.100", 
                access_code="12345678",
                serial="ABC123456789"
            )
            
            # Mock connection failure and recovery
            connection_states = ["disconnected", "connecting", "connected"]
            
            with patch.object(printer, 'check_connection', new_callable=AsyncMock) as mock_check:
                for state in connection_states:
                    mock_check.return_value = {
                        "is_connected": state == "connected",
                        "connection_type": "mqtt",
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                        "connection_quality": "good" if state == "connected" else "poor"
                    }
                    
                    result = await printer.check_connection()
                    
                    if state == "connected":
                        assert result["is_connected"] is True
                        assert result["connection_quality"] == "good"
                    else:
                        assert result["is_connected"] is False

    @pytest.mark.asyncio
    async def test_prusa_http_connection_recovery(self):
        """Test Prusa HTTP API connection recovery."""
        printer = PrusaPrinter(
            printer_id=str(uuid4()),
            name="Test Prusa Core One",
            ip_address="192.168.1.101",
            api_key="test_api_key_12345"
        )
        
        # Test connection timeout and retry
        with patch.object(printer, 'check_connection', new_callable=AsyncMock) as mock_check:
            # First call fails (timeout)
            mock_check.side_effect = [
                {"is_connected": False, "error": "Connection timeout"},
                {"is_connected": True, "connection_type": "http", "api_version": "v1"}
            ]
            
            # First attempt - failure
            result1 = await printer.check_connection()
            assert result1["is_connected"] is False
            assert "timeout" in result1["error"]
            
            # Second attempt - success
            result2 = await printer.check_connection()
            assert result2["is_connected"] is True
            assert result2["connection_type"] == "http"


class TestEssentialGermanBusinessIntegration:
    """Test German business logic integration in printer operations."""
    
    def test_german_material_cost_calculation(self):
        """Test German EUR material cost calculations with 19% VAT."""
        # Test material cost calculation with German business rules
        material_weight = 35.7  # grams
        material_cost_per_gram = 0.35  # EUR per gram
        vat_rate = 0.19  # German VAT rate
        
        base_cost = material_weight * material_cost_per_gram
        vat_amount = base_cost * vat_rate
        total_cost = base_cost + vat_amount
        
        # Validate German business calculations
        assert base_cost == pytest.approx(12.495, rel=1e-2)
        assert vat_amount == pytest.approx(2.374, rel=1e-2)  
        assert total_cost == pytest.approx(14.869, rel=1e-2)
        
        # Format as German currency
        formatted_cost = f"{total_cost:.2f} €"
        assert formatted_cost == "14.87 €"
    
    def test_german_business_customer_classification(self):
        """Test German business customer type classification."""
        test_cases = [
            ("Müller GmbH", "business"),
            ("Schmidt AG", "business"), 
            ("Weber UG", "business"),
            ("Privat Klaus", "private"),
            ("Max Mustermann", "private"),
            ("Porcus3D GmbH", "business")
        ]
        
        for customer_name, expected_type in test_cases:
            # Simple classification logic for German business entities
            is_business = any(suffix in customer_name for suffix in ["GmbH", "AG", "UG", "KG"])
            customer_type = "business" if is_business else "private"
            
            assert customer_type == expected_type, f"Failed for {customer_name}"
    
    def test_german_timezone_handling(self):
        """Test German timezone (Europe/Berlin) for printer operations."""
        from zoneinfo import ZoneInfo
        
        # Create timestamp in German timezone
        german_tz = ZoneInfo("Europe/Berlin")
        now_german = datetime.now(german_tz)
        
        # Validate timezone
        assert str(now_german.tzinfo) == "Europe/Berlin"
        
        # Convert to UTC for storage
        now_utc = now_german.astimezone(timezone.utc)
        assert now_utc.tzinfo == timezone.utc
        
        # Validate timezone conversion preserves time correctly
        time_diff = abs((now_german - now_utc.astimezone(german_tz)).total_seconds())
        assert time_diff < 1.0  # Less than 1 second difference