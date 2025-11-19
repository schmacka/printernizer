"""
Test suite for Settings API endpoints
Tests all settings-related API functionality including application settings,
printer configurations, and watch folders.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestSettingsAPI:
    """Test settings management API endpoints"""

    def test_get_application_settings(self, client, test_app):
        """Test GET /api/v1/settings/application - Get all application settings"""
        from unittest.mock import Mock

        # Mock the config service
        mock_config_service = Mock()
        mock_config_service.get_application_settings.return_value = {
            'database_path': '/data/printernizer.db',
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False,
            'environment': 'production',
            'log_level': 'INFO',
            'timezone': 'Europe/Berlin',
            'currency': 'EUR',
            'vat_rate': 19.0,
            'downloads_path': '/data/downloads',
            'max_file_size': 104857600,
            'monitoring_interval': 5,
            'connection_timeout': 10,
            'cors_origins': ['*'],
            'job_creation_auto_create': True,
            'gcode_optimize_print_only': True,
            'gcode_optimization_max_lines': 50000,
            'gcode_render_max_lines': 10000,
            'enable_upload': True,
            'max_upload_size_mb': 100,
            'allowed_upload_extensions': '.stl,.3mf,.gcode',
            'library_enabled': True,
            'library_path': '/data/library',
            'library_auto_organize': True,
            'library_auto_extract_metadata': True,
            'library_auto_deduplicate': False,
            'library_preserve_originals': True,
            'library_checksum_algorithm': 'sha256',
            'library_processing_workers': 2,
            'library_search_enabled': True,
            'library_search_min_length': 3,
            'timelapse_enabled': False,
            'timelapse_source_folder': '',
            'timelapse_output_folder': '',
            'timelapse_output_strategy': 'job',
            'timelapse_auto_process_timeout': 300,
            'timelapse_cleanup_age_days': 30,
        }
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        response = client.get("/api/v1/settings/application")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            'database_path', 'host', 'port', 'debug', 'environment', 'log_level',
            'timezone', 'currency', 'vat_rate', 'downloads_path', 'max_file_size',
            'monitoring_interval', 'connection_timeout', 'cors_origins',
            'job_creation_auto_create',
            'gcode_optimize_print_only', 'gcode_optimization_max_lines', 'gcode_render_max_lines',
            'enable_upload', 'max_upload_size_mb', 'allowed_upload_extensions',
            'library_enabled', 'library_path', 'library_auto_organize',
            'library_auto_extract_metadata', 'library_auto_deduplicate',
            'library_preserve_originals', 'library_checksum_algorithm',
            'library_processing_workers', 'library_search_enabled', 'library_search_min_length',
            'timelapse_enabled', 'timelapse_source_folder', 'timelapse_output_folder',
            'timelapse_output_strategy', 'timelapse_auto_process_timeout', 'timelapse_cleanup_age_days',
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_update_application_settings(self, client, test_app):
        """Test PUT /api/v1/settings/application - Update application settings"""
        from unittest.mock import Mock

        mock_config_service = Mock()
        mock_config_service.update_application_settings.return_value = True
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        update_data = {
            'log_level': 'DEBUG',
            'monitoring_interval': 10,
            'vat_rate': 19.5,
            'job_creation_auto_create': False,
            'library_enabled': True,
        }

        response = client.put("/api/v1/settings/application", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'updated_fields' in data
        assert len(data['updated_fields']) == 5

    def test_update_application_settings_no_changes(self, client, test_app):
        """Test PUT /api/v1/settings/application with no changes"""
        from unittest.mock import Mock

        mock_config_service = Mock()
        mock_config_service.update_application_settings.return_value = False
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        response = client.put("/api/v1/settings/application", json={})

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['updated_fields'] == []

    def test_get_watch_folder_settings(self, client, test_app):
        """Test GET /api/v1/settings/watch-folders - Get watch folder settings"""
        from unittest.mock import Mock, AsyncMock

        mock_config_service = Mock()
        mock_config_service.get_watch_folder_settings = AsyncMock(return_value={
            'watch_folders': ['/data/watch1', '/data/watch2'],
            'enabled': True,
            'recursive': False,
            'supported_extensions': ['.stl', '.3mf', '.gcode']
        })
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        response = client.get("/api/v1/settings/watch-folders")

        assert response.status_code == 200
        data = response.json()
        assert 'watch_folders' in data
        assert 'enabled' in data
        assert 'recursive' in data
        assert 'supported_extensions' in data
        assert len(data['watch_folders']) == 2


class TestSettingsValidation:
    """Test settings validation endpoints"""

    def test_validate_downloads_path_success(self, client, test_app):
        """Test POST /api/v1/settings/downloads-path/validate - Valid path"""
        from unittest.mock import Mock

        mock_config_service = Mock()
        mock_config_service.validate_downloads_path.return_value = {
            'valid': True,
            'message': 'Path is valid and writable'
        }
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        response = client.post("/api/v1/settings/downloads-path/validate?folder_path=/data/downloads")

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True

    def test_validate_library_path_success(self, client, test_app):
        """Test POST /api/v1/settings/library-path/validate - Valid path"""
        from unittest.mock import Mock

        mock_config_service = Mock()
        mock_config_service.validate_library_path.return_value = {
            'valid': True,
            'message': 'Path is valid and writable'
        }
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        response = client.post("/api/v1/settings/library-path/validate?folder_path=/data/library")

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True


class TestSettingsAccessibility:
    """Test that all settings fields are accessible and properly defined"""

    def test_all_general_settings_accessible(self, client, test_app):
        """Test that all general settings fields are accessible via API"""
        from unittest.mock import Mock

        mock_config_service = Mock()
        mock_config_service.get_application_settings.return_value = {
            'database_path': '/data/printernizer.db',
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False,
            'environment': 'production',
            'log_level': 'INFO',
            'timezone': 'Europe/Berlin',
            'currency': 'EUR',
            'vat_rate': 19.0,
            'downloads_path': '/data/downloads',
            'max_file_size': 104857600,
            'monitoring_interval': 5,
            'connection_timeout': 10,
            'cors_origins': ['*'],
            'job_creation_auto_create': True,
            'gcode_optimize_print_only': True,
            'gcode_optimization_max_lines': 50000,
            'gcode_render_max_lines': 10000,
            'enable_upload': True,
            'max_upload_size_mb': 100,
            'allowed_upload_extensions': '.stl,.3mf,.gcode',
            'library_enabled': True,
            'library_path': '/data/library',
            'library_auto_organize': True,
            'library_auto_extract_metadata': True,
            'library_auto_deduplicate': False,
            'library_preserve_originals': True,
            'library_checksum_algorithm': 'sha256',
            'library_processing_workers': 2,
            'library_search_enabled': True,
            'library_search_min_length': 3,
            'timelapse_enabled': False,
            'timelapse_source_folder': '',
            'timelapse_output_folder': '',
            'timelapse_output_strategy': 'job',
            'timelapse_auto_process_timeout': 300,
            'timelapse_cleanup_age_days': 30,
        }
        test_app.dependency_overrides[test_app.state.get_config_service] = lambda: mock_config_service

        response = client.get("/api/v1/settings/application")
        assert response.status_code == 200

        data = response.json()

        # General settings
        assert 'log_level' in data
        assert 'monitoring_interval' in data
        assert 'connection_timeout' in data
        assert 'vat_rate' in data
        assert 'timezone' in data
        assert 'currency' in data

        # Job creation settings
        assert 'job_creation_auto_create' in data

        # G-code settings
        assert 'gcode_optimize_print_only' in data
        assert 'gcode_optimization_max_lines' in data
        assert 'gcode_render_max_lines' in data

        # Library settings
        assert 'library_enabled' in data
        assert 'library_path' in data
        assert 'library_auto_organize' in data
        assert 'library_auto_extract_metadata' in data
        assert 'library_auto_deduplicate' in data
        assert 'library_preserve_originals' in data
        assert 'library_checksum_algorithm' in data
        assert 'library_processing_workers' in data
        assert 'library_search_enabled' in data
        assert 'library_search_min_length' in data

        # File settings
        assert 'downloads_path' in data
        assert 'max_file_size' in data
        assert 'enable_upload' in data
        assert 'max_upload_size_mb' in data
        assert 'allowed_upload_extensions' in data

        # Timelapse settings
        assert 'timelapse_enabled' in data
        assert 'timelapse_source_folder' in data
        assert 'timelapse_output_folder' in data
        assert 'timelapse_output_strategy' in data
        assert 'timelapse_auto_process_timeout' in data
        assert 'timelapse_cleanup_age_days' in data
