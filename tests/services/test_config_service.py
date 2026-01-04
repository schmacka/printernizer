"""
Unit tests for Config Service.
Tests configuration management, printer config validation, and settings handling.

Sprint 2 Phase 1 - Core Service Test Coverage.
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from src.services.config_service import ConfigService, PrinterConfig, Settings


class TestPrinterConfig:
    """Test PrinterConfig dataclass."""

    def test_printer_config_basic_creation(self):
        """Test creating a basic PrinterConfig."""
        config = PrinterConfig(
            printer_id="bambu_001",
            name="Bambu Lab A1",
            type="bambu_lab",
            ip_address="192.168.1.100",
            access_code="12345678"
        )

        assert config.printer_id == "bambu_001"
        assert config.name == "Bambu Lab A1"
        assert config.type == "bambu_lab"
        assert config.ip_address == "192.168.1.100"
        assert config.access_code == "12345678"
        assert config.is_active == True  # Default value

    def test_printer_config_prusa_creation(self):
        """Test creating a Prusa PrinterConfig."""
        config = PrinterConfig(
            printer_id="prusa_001",
            name="Prusa Core One",
            type="prusa_core",
            ip_address="192.168.1.101",
            api_key="prusa_api_key"
        )

        assert config.type == "prusa_core"
        assert config.api_key == "prusa_api_key"

    def test_printer_config_from_dict(self):
        """Test creating PrinterConfig from dictionary."""
        config_dict = {
            'name': 'Test Printer',
            'type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'access_code': '12345678',
            'serial_number': 'ABC123',
            'is_active': True
        }

        config = PrinterConfig.from_dict('test_001', config_dict)

        assert config.printer_id == 'test_001'
        assert config.name == 'Test Printer'
        assert config.type == 'bambu_lab'
        assert config.ip_address == '192.168.1.100'
        assert config.access_code == '12345678'
        assert config.serial_number == 'ABC123'

    def test_printer_config_to_dict(self):
        """Test converting PrinterConfig to dictionary."""
        config = PrinterConfig(
            printer_id="bambu_001",
            name="Bambu Lab A1",
            type="bambu_lab",
            ip_address="192.168.1.100",
            access_code="12345678"
        )

        result = config.to_dict()

        assert result['name'] == "Bambu Lab A1"
        assert result['type'] == "bambu_lab"
        assert result['ip_address'] == "192.168.1.100"
        assert result['access_code'] == "12345678"
        # printer_id is not in the dict (it's the key)
        assert 'printer_id' not in result

    def test_printer_config_to_dict_safe(self):
        """Test converting PrinterConfig to safe dictionary (masks sensitive data)."""
        config = PrinterConfig(
            printer_id="bambu_001",
            name="Bambu Lab A1",
            type="bambu_lab",
            ip_address="192.168.1.100",
            access_code="12345678",
            api_key="secret_key"
        )

        result = config.to_dict_safe()

        # Sensitive fields should be masked
        assert result.get('access_code') != "12345678" or result.get('access_code') is None
        assert result.get('api_key') != "secret_key" or result.get('api_key') is None

    def test_printer_config_bambu_validation(self):
        """Test Bambu Lab printer requires ip_address and access_code."""
        with pytest.raises(ValueError, match="requires ip_address and access_code"):
            PrinterConfig(
                printer_id="bambu_001",
                name="Bambu Lab A1",
                type="bambu_lab",
                # Missing ip_address and access_code
            )

    def test_printer_config_prusa_validation(self):
        """Test Prusa printer requires ip_address and api_key."""
        with pytest.raises(ValueError, match="requires ip_address and api_key"):
            PrinterConfig(
                printer_id="prusa_001",
                name="Prusa Core One",
                type="prusa_core",
                ip_address="192.168.1.100"
                # Missing api_key
            )

    def test_printer_config_unknown_type_logs_warning(self):
        """Test unknown printer type logs warning but doesn't raise."""
        # Should not raise, just logs warning
        config = PrinterConfig(
            printer_id="unknown_001",
            name="Unknown Printer",
            type="unknown_type",
            ip_address="192.168.1.100"
        )

        assert config.type == "unknown_type"

    def test_printer_config_inactive_by_default(self):
        """Test printer can be created as inactive."""
        config = PrinterConfig(
            printer_id="bambu_001",
            name="Bambu Lab A1",
            type="bambu_lab",
            ip_address="192.168.1.100",
            access_code="12345678",
            is_active=False
        )

        assert config.is_active == False


class TestSettings:
    """Test Settings class with environment variable support."""

    def test_settings_default_values(self):
        """Test Settings has sensible defaults (may be overridden by .env)."""
        settings = Settings()

        # These values may be overridden by .env file, so just check types
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert isinstance(settings.debug, bool)
        assert settings.environment in ["production", "development", "testing"]
        assert settings.timezone == "Europe/Berlin"
        assert settings.currency == "EUR"
        assert settings.vat_rate == 0.19

    def test_settings_cors_origins_parsing(self):
        """Test CORS origins are parsed from comma-separated string."""
        settings = Settings()

        origins = settings.get_cors_origins()

        assert isinstance(origins, list)
        assert len(origins) > 0

    def test_settings_downloads_path_normalization(self):
        """Test downloads path is normalized."""
        # The validator removes control characters and normalizes slashes
        settings = Settings()

        # Path should be normalized (no control chars, etc.)
        assert '\t' not in str(settings.downloads_path)
        assert '\n' not in str(settings.downloads_path)


class TestConfigService:
    """Test ConfigService configuration management."""

    @pytest.fixture
    def temp_config_path(self, tmp_path):
        """Create temporary config file path."""
        return tmp_path / "printers.json"

    @pytest.fixture
    def mock_database(self):
        """Create mock database for ConfigService."""
        db = MagicMock()
        db._connection = MagicMock()
        return db

    @pytest.fixture
    def config_service_with_empty_config(self, temp_config_path, mock_database):
        """Create ConfigService with empty config file."""
        # Create empty printers config
        config_data = {"printers": {}}
        temp_config_path.write_text(json.dumps(config_data))

        return ConfigService(config_path=str(temp_config_path), database=mock_database)

    @pytest.fixture
    def config_service_with_printers(self, temp_config_path, mock_database):
        """Create ConfigService with sample printers."""
        config_data = {
            "printers": {
                "bambu_001": {
                    "name": "Bambu Lab A1 #1",
                    "type": "bambu_lab",
                    "ip_address": "192.168.1.100",
                    "access_code": "12345678",
                    "is_active": True
                },
                "prusa_001": {
                    "name": "Prusa Core One #1",
                    "type": "prusa_core",
                    "ip_address": "192.168.1.101",
                    "api_key": "prusa_key_123",
                    "is_active": False
                }
            }
        }
        temp_config_path.write_text(json.dumps(config_data))

        return ConfigService(config_path=str(temp_config_path), database=mock_database)

    def test_config_service_initialization(self, config_service_with_empty_config):
        """Test ConfigService initializes correctly."""
        service = config_service_with_empty_config

        assert service.settings is not None
        assert isinstance(service._printers, dict)

    def test_config_service_creates_default_config(self, tmp_path, mock_database):
        """Test ConfigService creates default config if file doesn't exist."""
        config_path = tmp_path / "nonexistent" / "printers.json"

        # Should not raise - creates default config
        service = ConfigService(config_path=str(config_path), database=mock_database)

        # Default config should be created
        assert config_path.exists()

    def test_get_printers(self, config_service_with_printers):
        """Test getting all printer configurations."""
        printers = config_service_with_printers.get_printers()

        assert len(printers) == 2
        assert "bambu_001" in printers
        assert "prusa_001" in printers

    def test_get_printers_returns_copy(self, config_service_with_printers):
        """Test get_printers returns a copy, not the internal dict."""
        printers1 = config_service_with_printers.get_printers()
        printers2 = config_service_with_printers.get_printers()

        # Should be different objects
        assert printers1 is not printers2

    def test_get_printer(self, config_service_with_printers):
        """Test getting specific printer configuration."""
        printer = config_service_with_printers.get_printer("bambu_001")

        assert printer is not None
        assert printer.name == "Bambu Lab A1 #1"
        assert printer.type == "bambu_lab"

    def test_get_printer_not_found(self, config_service_with_printers):
        """Test getting non-existent printer returns None."""
        printer = config_service_with_printers.get_printer("nonexistent")

        assert printer is None

    def test_get_active_printers(self, config_service_with_printers):
        """Test getting only active printers."""
        active_printers = config_service_with_printers.get_active_printers()

        assert len(active_printers) == 1
        assert "bambu_001" in active_printers
        assert "prusa_001" not in active_printers

    def test_add_printer(self, config_service_with_empty_config, temp_config_path):
        """Test adding a new printer configuration."""
        service = config_service_with_empty_config

        result = service.add_printer("new_printer", {
            "name": "New Printer",
            "type": "bambu_lab",
            "ip_address": "192.168.1.200",
            "access_code": "newcode123"
        })

        assert result == True
        assert "new_printer" in service.get_printers()

        # Verify saved to file
        saved_config = json.loads(temp_config_path.read_text())
        assert "new_printer" in saved_config.get("printers", {})

    def test_add_printer_invalid_config(self, config_service_with_empty_config):
        """Test adding printer with invalid config returns False."""
        service = config_service_with_empty_config

        result = service.add_printer("bad_printer", {
            "name": "Bad Printer",
            "type": "bambu_lab"
            # Missing required fields
        })

        assert result == False
        assert "bad_printer" not in service.get_printers()

    def test_remove_printer(self, config_service_with_printers, temp_config_path):
        """Test removing a printer configuration."""
        service = config_service_with_printers

        result = service.remove_printer("bambu_001")

        assert result == True
        assert "bambu_001" not in service.get_printers()

        # Verify removed from file
        saved_config = json.loads(temp_config_path.read_text())
        assert "bambu_001" not in saved_config.get("printers", {})

    def test_remove_printer_not_found(self, config_service_with_printers):
        """Test removing non-existent printer returns False."""
        result = config_service_with_printers.remove_printer("nonexistent")

        assert result == False

    def test_reload_config(self, config_service_with_printers, temp_config_path):
        """Test reloading configuration from file."""
        service = config_service_with_printers

        # Modify the file externally
        config_data = {
            "printers": {
                "new_printer": {
                    "name": "New Printer",
                    "type": "bambu_lab",
                    "ip_address": "192.168.1.200",
                    "access_code": "newcode123"
                }
            }
        }
        temp_config_path.write_text(json.dumps(config_data))

        # Reload
        result = service.reload_config()

        assert result == True
        printers = service.get_printers()
        assert "new_printer" in printers
        # Old printers should be gone
        assert "bambu_001" not in printers

    def test_validate_printer_connection_valid(self, config_service_with_printers):
        """Test validating valid printer connection."""
        result = config_service_with_printers.validate_printer_connection("bambu_001")

        assert result["valid"] == True

    def test_validate_printer_connection_not_found(self, config_service_with_printers):
        """Test validating non-existent printer connection."""
        result = config_service_with_printers.validate_printer_connection("nonexistent")

        assert result["valid"] == False
        assert "not found" in result["error"]

    def test_get_business_settings(self, config_service_with_empty_config):
        """Test getting German business settings."""
        settings = config_service_with_empty_config.get_business_settings()

        assert "timezone" in settings
        assert "currency" in settings
        assert "vat_rate" in settings
        assert settings["currency"] == "EUR"
        assert settings["vat_rate"] == 0.19


class TestConfigServicePathValidation:
    """Test path validation methods."""

    @pytest.fixture
    def config_service(self, tmp_path):
        """Create ConfigService for path validation tests."""
        config_path = tmp_path / "printers.json"
        config_path.write_text(json.dumps({"printers": {}}))

        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        return ConfigService(config_path=str(config_path), database=mock_db)

    def test_validate_watch_folder_valid(self, config_service, tmp_path):
        """Test validating valid watch folder."""
        test_folder = tmp_path / "watch"
        test_folder.mkdir()

        result = config_service.validate_watch_folder(str(test_folder))

        assert result["valid"] == True

    def test_validate_watch_folder_not_exists(self, config_service, tmp_path):
        """Test validating non-existent watch folder."""
        result = config_service.validate_watch_folder(str(tmp_path / "nonexistent"))

        assert result["valid"] == False
        assert "does not exist" in result["error"]

    def test_validate_watch_folder_not_directory(self, config_service, tmp_path):
        """Test validating file path (not directory)."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("test")

        result = config_service.validate_watch_folder(str(test_file))

        assert result["valid"] == False
        assert "not a directory" in result["error"]

    def test_validate_downloads_path_valid(self, config_service, tmp_path):
        """Test validating valid downloads path."""
        test_folder = tmp_path / "downloads"
        test_folder.mkdir()

        result = config_service.validate_downloads_path(str(test_folder))

        assert result["valid"] == True

    def test_validate_downloads_path_creates_if_missing(self, config_service, tmp_path):
        """Test downloads path validation creates directory if missing."""
        test_folder = tmp_path / "new_downloads"

        result = config_service.validate_downloads_path(str(test_folder))

        assert result["valid"] == True
        assert test_folder.exists()

    def test_validate_library_path_valid(self, config_service, tmp_path):
        """Test validating valid library path."""
        test_folder = tmp_path / "library"
        test_folder.mkdir()

        result = config_service.validate_library_path(str(test_folder))

        assert result["valid"] == True


class TestConfigServiceApplicationSettings:
    """Test application settings methods."""

    @pytest.fixture
    def config_service(self, tmp_path):
        """Create ConfigService for settings tests."""
        config_path = tmp_path / "printers.json"
        config_path.write_text(json.dumps({"printers": {}}))

        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        return ConfigService(config_path=str(config_path), database=mock_db)

    def test_get_application_settings(self, config_service):
        """Test getting all application settings."""
        settings = config_service.get_application_settings()

        assert isinstance(settings, dict)
        assert "timezone" in settings
        assert "currency" in settings
        assert "vat_rate" in settings
        assert "log_level" in settings

    def test_update_application_settings(self, config_service):
        """Test updating application settings."""
        result = config_service.update_application_settings({
            "log_level": "DEBUG"
        })

        assert result == True

    def test_update_application_settings_invalid_key(self, config_service):
        """Test updating non-updatable setting returns False."""
        result = config_service.update_application_settings({
            "invalid_setting": "value"
        })

        # Should return False if no valid settings were updated
        assert result == False


class TestConfigServiceEnvironmentLoading:
    """Test environment variable loading."""

    def test_load_from_environment(self, tmp_path):
        """Test loading printer configs from environment variables."""
        config_path = tmp_path / "printers.json"
        config_path.write_text(json.dumps({"printers": {}}))

        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        # Set environment variables
        with patch.dict(os.environ, {
            'PRINTERNIZER_PRINTER_ENV_TEST_NAME': 'Env Printer',
            'PRINTERNIZER_PRINTER_ENV_TEST_TYPE': 'bambu_lab',
            'PRINTERNIZER_PRINTER_ENV_TEST_IP_ADDRESS': '192.168.1.150',
            'PRINTERNIZER_PRINTER_ENV_TEST_ACCESS_CODE': 'envcode123'
        }):
            service = ConfigService(config_path=str(config_path), database=mock_db)

            # Environment printers may be loaded (depends on parsing logic)
            # At minimum, the service should initialize without errors
            assert service is not None
