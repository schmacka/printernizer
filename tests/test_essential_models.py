"""
Essential model validation tests for Printernizer Milestone 1.1
Tests core data model validation without over-testing.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.printer import Printer, PrinterType, PrinterStatus, PrinterConfig
from src.models.job import Job, JobStatus, JobCreate, JobUpdate
from src.models.file import File, FileStatus


class TestPrinterModel:
    """Test essential Printer model validation."""

    def test_valid_bambu_printer_creation(self):
        """Test creating valid Bambu Lab printer."""
        printer_data = {
            "id": "bambu_001",
            "name": "Bambu A1 #1",
            "type": PrinterType.BAMBU_LAB,
            "ip_address": "192.168.1.100",
            "access_code": "test_code",
            "serial_number": "AC12345678"
        }
        
        printer = Printer(**printer_data)
        
        assert printer.id == "bambu_001"
        assert printer.type == PrinterType.BAMBU_LAB
        assert printer.is_active is True  # Default value
        assert printer.status == PrinterStatus.UNKNOWN  # Default

    def test_valid_prusa_printer_creation(self):
        """Test creating valid Prusa printer."""
        printer_data = {
            "id": "prusa_001", 
            "name": "Prusa Core One #1",
            "type": PrinterType.PRUSA_CORE,
            "ip_address": "192.168.1.101",
            "api_key": "test_api_key_123"
        }
        
        printer = Printer(**printer_data)
        
        assert printer.type == PrinterType.PRUSA_CORE
        assert printer.api_key == "test_api_key_123"

    def test_printer_required_fields(self):
        """Test printer validation fails without required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Printer()  # Missing required fields
        
        errors = exc_info.value.errors()
        required_fields = ["id", "name", "type"]
        
        error_fields = [error["loc"][0] for error in errors]
        for field in required_fields:
            assert field in error_fields

    def test_printer_config_optional_fields(self):
        """Test PrinterConfig with optional updates."""
        config = PrinterConfig(name="Updated Name", is_active=False)
        
        assert config.name == "Updated Name"
        assert config.is_active is False
        assert config.ip_address is None  # Optional


class TestJobModel:
    """Test essential Job model validation."""

    def test_valid_job_creation(self):
        """Test creating valid print job."""
        job_data = {
            "id": "job_001",
            "printer_id": "bambu_001", 
            "printer_type": "bambu_lab",
            "job_name": "test_cube.3mf",
            "is_business": True
        }
        
        job = Job(**job_data)
        
        assert job.id == "job_001"
        assert job.is_business is True
        assert job.status == JobStatus.PENDING  # Default

    def test_job_business_logic_fields(self):
        """Test German business-specific job fields."""
        job = Job(
            id="business_job",
            printer_id="bambu_001",
            printer_type="bambu_lab", 
            job_name="customer_order.3mf",
            is_business=True,
            material_used=25.5,
            material_cost=1.28,  # 25.5g * 0.05 EUR/g
            power_cost=0.75
        )
        
        assert job.is_business is True
        assert job.material_cost == 1.28
        assert job.power_cost == 0.75

    def test_job_create_minimal(self):
        """Test minimal JobCreate validation."""
        job_create = JobCreate(
            printer_id="printer_001",
            job_name="test_print.stl"
        )
        
        assert job_create.printer_id == "printer_001"
        assert job_create.is_business is False  # Default

    def test_job_update_fields(self):
        """Test JobUpdate validation."""
        update = JobUpdate(
            status=JobStatus.COMPLETED,
            progress=100,
            material_used=30.2
        )
        
        assert update.status == JobStatus.COMPLETED
        assert update.progress == 100


class TestFileModel:
    """Test essential File model validation."""

    def test_valid_file_creation(self):
        """Test creating valid file record."""
        file_data = {
            "id": "file_001",
            "printer_id": "bambu_001",
            "filename": "test_cube.3mf",
            "file_size": 1024000,
            "file_path": "/storage/test_cube.3mf"
        }
        
        file_obj = File(**file_data)
        
        assert file_obj.filename == "test_cube.3mf"
        assert file_obj.status == FileStatus.AVAILABLE  # Default

    def test_file_download_status_progression(self):
        """Test file download status changes."""
        # Available file
        file_obj = File(
            id="file_001",
            printer_id="printer_001",
            filename="test.stl",
            file_size=500000,
            status=FileStatus.AVAILABLE
        )
        assert file_obj.status == FileStatus.AVAILABLE

        # Downloaded file
        downloaded_file = File(
            id="file_002",
            printer_id="printer_001",
            filename="downloaded.stl",
            file_size=600000,
            status=FileStatus.DOWNLOADED,
            file_path="/downloads/downloaded.stl"
        )
        assert downloaded_file.status == FileStatus.DOWNLOADED
        assert downloaded_file.file_path is not None


class TestEnumValidation:
    """Test enum validation for consistency."""

    def test_printer_type_enum_values(self):
        """Test PrinterType enum has expected values."""
        assert PrinterType.BAMBU_LAB == "bambu_lab"
        assert PrinterType.PRUSA_CORE == "prusa_core"
        assert PrinterType.UNKNOWN == "unknown"

    def test_printer_status_enum_values(self):
        """Test PrinterStatus enum covers essential states."""
        essential_statuses = ["online", "offline", "printing", "error", "unknown"]
        
        for status in essential_statuses:
            assert hasattr(PrinterStatus, status.upper())

    def test_job_status_enum_values(self):
        """Test JobStatus enum covers print lifecycle."""
        job_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        
        for status in job_statuses:
            assert hasattr(JobStatus, status.upper())

    def test_file_download_status_enum(self):
        """Test FileStatus enum for file management."""
        assert FileStatus.AVAILABLE == "available"
        assert FileStatus.DOWNLOADING == "downloading"
        assert FileStatus.DOWNLOADED == "downloaded"
        assert FileStatus.ERROR == "error"


class TestModelSerialization:
    """Test model JSON serialization for API responses."""

    def test_printer_json_serialization(self):
        """Test printer serializes to valid JSON."""
        printer = Printer(
            id="test_printer",
            name="Test Printer", 
            type=PrinterType.BAMBU_LAB,
            created_at=datetime.now()
        )
        
        json_data = printer.model_dump()
        
        assert "id" in json_data
        assert "created_at" in json_data
        assert json_data["type"] == "bambu_lab"

    def test_job_json_serialization(self):
        """Test job serializes with German business fields."""
        job = Job(
            id="test_job",
            printer_id="printer_001",
            printer_type="bambu_lab",
            job_name="business_order.3mf",
            is_business=True,
            material_cost=2.50
        )
        
        json_data = job.model_dump()
        
        assert json_data["is_business"] is True
        assert json_data["material_cost"] == 2.50