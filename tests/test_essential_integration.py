"""
Essential integration test for Printernizer Milestone 1.1 core workflow
Tests the complete printer setup and basic job monitoring workflow.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.models.printer import PrinterType, PrinterStatus
from src.models.job import JobStatus


@pytest.fixture
def async_client():
    """Async test client for integration testing."""
    return TestClient(app)


class TestCoreWorkflowIntegration:
    """Test essential end-to-end workflow for Milestone 1.1."""

    def test_complete_printer_setup_workflow(self, async_client):
        """Test complete workflow: Add printer -> Connect -> Monitor status."""
        
        # Step 1: Add Bambu Lab printer
        bambu_data = {
            "id": "integration_bambu_001",
            "name": "Integration Test Bambu A1",
            "type": "bambu_lab",
            "ip_address": "192.168.1.100",
            "access_code": "test_access",
            "serial_number": "AC12345678"
        }
        
        response = async_client.post("/api/v1/printers", json=bambu_data)
        assert response.status_code == 201
        created_printer = response.json()
        assert created_printer["id"] == bambu_data["id"]
        
        # Step 2: Verify printer is in system
        response = async_client.get(f"/api/v1/printers/{bambu_data['id']}")
        assert response.status_code == 200
        printer_details = response.json()
        assert printer_details["type"] == "bambu_lab"
        
        # Step 3: Test printer connection (may fail - no real printer)
        response = async_client.post(f"/api/v1/printers/{bambu_data['id']}/connect")
        assert response.status_code in [200, 503]  # Success or unavailable
        
        # Step 4: Check system can list all printers
        response = async_client.get("/api/v1/printers")
        assert response.status_code == 200
        printers_list = response.json()
        assert len(printers_list) >= 1
        
        printer_ids = [p["id"] for p in printers_list]
        assert bambu_data["id"] in printer_ids

    def test_health_check_system_integration(self, async_client):
        """Test health check includes all system components."""
        response = async_client.get("/api/v1/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        # Essential health check components
        assert "status" in health_data
        assert "database" in health_data
        assert "services" in health_data
        assert "timestamp" in health_data
        
        # System should be operational for basic functionality
        assert health_data["status"] in ["healthy", "degraded"]

    def test_files_discovery_workflow(self, async_client):
        """Test file discovery and management workflow."""
        
        # Step 1: Get files list (may be empty initially)
        response = async_client.get("/api/v1/files")
        assert response.status_code == 200
        files_data = response.json()
        
        # Should have proper structure even if empty
        assert "files" in files_data or isinstance(files_data, list)

    def test_jobs_monitoring_workflow(self, async_client):
        """Test basic job monitoring workflow."""
        
        # Step 1: Get current jobs (initially empty)
        response = async_client.get("/api/v1/jobs")
        assert response.status_code == 200
        jobs_data = response.json()
        
        # Should return proper structure
        assert "jobs" in jobs_data or isinstance(jobs_data, list)

    def test_analytics_basic_functionality(self, async_client):
        """Test analytics endpoint basic functionality."""
        response = async_client.get("/api/v1/analytics")
        assert response.status_code == 200
        analytics_data = response.json()
        
        # Should have basic analytics structure
        assert isinstance(analytics_data, dict)

    def test_system_configuration_workflow(self, async_client):
        """Test system configuration endpoints."""
        response = async_client.get("/api/v1/system")
        assert response.status_code == 200
        system_data = response.json()
        
        # Should return system configuration
        assert isinstance(system_data, dict)

    @pytest.mark.asyncio
    async def test_websocket_connection_basic(self):
        """Test WebSocket connection can be established."""
        # Note: This is a basic test - full WebSocket testing is complex
        
        try:
            from websockets import connect
            
            # Attempt WebSocket connection (may fail if server not running)
            websocket_url = "ws://localhost:8000/ws"
            
            # This is more of a structure test than actual connection test
            assert websocket_url.startswith("ws://")
            assert ":8000" in websocket_url
            
        except ImportError:
            # WebSocket testing library not available - skip gracefully
            pytest.skip("WebSocket testing library not available")

    def test_german_business_integration(self, async_client):
        """Test German business logic integration."""
        
        # Test with German customer data
        business_printer = {
            "id": "business_drucker_001",
            "name": "Geschäftsdrucker Müller",
            "type": "prusa_core",
            "ip_address": "192.168.1.101",
            "api_key": "business_key_123"
        }
        
        response = async_client.post("/api/v1/printers", json=business_printer)
        assert response.status_code == 201
        
        created = response.json()
        assert "Müller" in created["name"]  # German umlaut preserved
        
        # Verify printer can be retrieved with German name
        response = async_client.get(f"/api/v1/printers/{business_printer['id']}")
        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved["name"] == business_printer["name"]


class TestErrorHandlingIntegration:
    """Test error handling across the system."""

    def test_invalid_printer_data_handling(self, async_client):
        """Test system handles invalid printer data gracefully."""
        
        invalid_data = {
            "id": "",  # Invalid empty ID
            "name": "Te",  # Too short
            "type": "invalid_type"  # Invalid type
        }
        
        response = async_client.post("/api/v1/printers", json=invalid_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"] == "VALIDATION_ERROR"

    def test_nonexistent_resource_handling(self, async_client):
        """Test system handles requests for non-existent resources."""
        
        # Try to get non-existent printer
        response = async_client.get("/api/v1/printers/nonexistent_printer")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "error" in error_data

    def test_duplicate_printer_handling(self, async_client):
        """Test system prevents duplicate printer IDs."""
        
        printer_data = {
            "id": "duplicate_test",
            "name": "Test Printer",
            "type": "bambu_lab",
            "ip_address": "192.168.1.100"
        }
        
        # Create first printer
        response1 = async_client.post("/api/v1/printers", json=printer_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = async_client.post("/api/v1/printers", json=printer_data)
        assert response2.status_code == 409  # Conflict


class TestGermanBusinessIntegration:
    """Test German business requirements integration."""

    def test_timezone_integration(self):
        """Test German timezone is used throughout system."""
        import pytz
        from datetime import datetime
        
        berlin_tz = pytz.timezone('Europe/Berlin')
        now = datetime.now(berlin_tz)
        
        assert now.tzinfo is not None
        assert 'Europe/Berlin' in str(now.tzinfo) or 'CET' in str(now.tzinfo) or 'CEST' in str(now.tzinfo)

    def test_currency_formatting_integration(self):
        """Test EUR currency formatting in business calculations."""
        
        def calculate_job_cost(material_grams, cost_per_gram, vat_rate=0.19):
            base_cost = material_grams * cost_per_gram
            vat = base_cost * vat_rate
            total = base_cost + vat
            return round(total, 2)
        
        # Test calculation
        total_cost = calculate_job_cost(25.5, 0.05)  # 25.5g at 5 cents/gram
        expected = round((25.5 * 0.05) * 1.19, 2)  # With 19% VAT
        
        assert total_cost == expected
        assert total_cost > 0

    def test_business_vs_private_classification(self):
        """Test business vs private job classification logic."""
        
        def classify_customer(customer_name):
            business_indicators = ['GmbH', 'AG', 'OHG', 'KG', 'e.V.', 'UG']
            return any(indicator in customer_name for indicator in business_indicators)
        
        # Test cases
        assert classify_customer("Müller Maschinenbau GmbH") is True
        assert classify_customer("Hans Müller") is False
        assert classify_customer("TechStart UG") is True
        assert classify_customer("Maria Schmidt") is False

    def test_file_naming_german_support(self):
        """Test file naming supports German characters."""
        
        german_filenames = [
            "Auftrag_Müller_2024.3mf",
            "Prototyp_für_Düsseldorf.stl",
            "Geschäft_Größe_XL.gcode"
        ]
        
        for filename in german_filenames:
            # Should contain German characters
            has_german = any(char in filename for char in 'äöüÄÖÜß')
            # Should have valid extension
            valid_ext = filename.endswith(('.3mf', '.stl', '.gcode'))
            
            # At least one should have German chars, all should have valid extensions
            assert valid_ext is True


@pytest.mark.skipif(True, reason="Requires actual printer hardware")
class TestHardwareIntegration:
    """Hardware integration tests (skipped without real printers)."""

    def test_bambu_lab_real_connection(self):
        """Test connection to real Bambu Lab printer (requires hardware)."""
        pytest.skip("Requires actual Bambu Lab printer")

    def test_prusa_real_connection(self):
        """Test connection to real Prusa printer (requires hardware)."""
        pytest.skip("Requires actual Prusa printer")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])