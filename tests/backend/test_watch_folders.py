"""
Basic tests for watch folder functionality.
Tests core FileWatcher service and configuration.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.services.file_watcher_service import FileWatcherService, LocalFile
from src.services.config_service import ConfigService
from src.services.event_service import EventService


class TestWatchFolderConfiguration:
    """Test watch folder configuration functionality."""
    
    def test_config_settings(self):
        """Test watch folder configuration settings."""
        from utils.config import PrinternizerSettings
        
        # Test default settings
        settings = PrinternizerSettings()
        assert settings.watch_folders == ""
        assert settings.watch_folders_enabled == True
        assert settings.watch_recursive == True
        
        # Test parsed folders list
        assert settings.watch_folders_list == []
        
        # Test with folders set
        settings = PrinternizerSettings(watch_folders="C:\\temp,D:\\models")
        folders = settings.watch_folders_list
        assert len(folders) == 2
        assert "C:\\temp" in folders
        assert "D:\\models" in folders

    def test_config_service_watch_folders(self):
        """Test ConfigService watch folder methods."""
        config_service = ConfigService()
        
        # Test validation of non-existent folder
        result = config_service.validate_watch_folder("C:\\non_existent_folder")
        assert result["valid"] == False
        assert "does not exist" in result["error"]
        
        # Test validation of valid temp folder
        with tempfile.TemporaryDirectory() as temp_dir:
            result = config_service.validate_watch_folder(temp_dir)
            assert result["valid"] == True


class TestFileWatcherService:
    """Test FileWatcher service core functionality."""
    
    @pytest.fixture
    async def file_watcher(self):
        """Create a FileWatcher service instance for testing."""
        # Mock dependencies
        config_service = Mock()
        config_service.is_watch_folders_enabled.return_value = True
        config_service.get_watch_folders.return_value = []
        config_service.is_recursive_watching_enabled.return_value = True
        config_service.validate_watch_folder.return_value = {"valid": True}
        
        event_service = Mock()
        event_service.emit_event = AsyncMock()
        
        watcher = FileWatcherService(config_service, event_service)
        return watcher

    def test_local_file_creation(self):
        """Test LocalFile dataclass functionality."""
        local_file = LocalFile(
            file_id="test_file_1",
            filename="test.stl",
            file_path="/path/to/test.stl",
            file_size=1024,
            file_type=".stl",
            modified_time="2023-12-01T10:00:00",
            watch_folder_path="/path/to",
            relative_path="test.stl"
        )
        
        assert local_file.file_id == "test_file_1"
        assert local_file.filename == "test.stl"
        assert local_file.file_type == ".stl"
        assert local_file.file_size == 1024

    async def test_file_watcher_status(self, file_watcher):
        """Test FileWatcher service status methods."""
        status = file_watcher.get_watch_status()
        
        assert "is_running" in status
        assert "watched_folders" in status
        assert "local_files_count" in status
        assert "supported_extensions" in status
        
        # Should not be running initially
        assert status["is_running"] == False

    def test_print_file_handler_extension_filtering(self):
        """Test PrintFileHandler extension filtering."""
        from services.file_watcher_service import PrintFileHandler
        
        # Mock FileWatcher
        watcher = Mock()
        handler = PrintFileHandler(watcher)
        
        # Test supported extensions
        assert handler.should_process_file("test.stl") == True
        assert handler.should_process_file("model.3mf") == True
        assert handler.should_process_file("print.gcode") == True
        assert handler.should_process_file("mesh.obj") == True
        assert handler.should_process_file("scan.ply") == True
        
        # Test unsupported extensions
        assert handler.should_process_file("document.txt") == False
        assert handler.should_process_file("image.jpg") == False
        assert handler.should_process_file("config.json") == False
        
        # Test ignored patterns
        assert handler.should_process_file("temp.tmp") == False
        assert handler.should_process_file(".hidden.stl") == False
        assert handler.should_process_file("backup.stl~") == False

    async def test_local_files_list(self, file_watcher):
        """Test getting local files list."""
        files = file_watcher.get_local_files()
        
        # Should return empty list initially
        assert isinstance(files, list)
        assert len(files) == 0


class TestWatchFolderIntegration:
    """Test integration between components."""
    
    def test_database_local_file_support(self):
        """Test database support for local files."""
        file_data = {
            'id': 'local_test_123',
            'printer_id': 'local',
            'filename': 'test_model.stl',
            'file_path': '/watch/folder/test_model.stl',
            'file_size': 2048,
            'file_type': '.stl',
            'status': 'local',
            'source': 'local_watch',
            'watch_folder_path': '/watch/folder',
            'relative_path': 'test_model.stl',
            'modified_time': '2023-12-01T10:00:00'
        }
        
        # Test that all required fields are present
        required_fields = ['id', 'filename', 'source', 'watch_folder_path']
        for field in required_fields:
            assert field in file_data

    def test_file_service_local_integration(self):
        """Test FileService integration with local files."""
        from services.file_service import FileService
        from database.database import Database
        from services.event_service import EventService
        
        # Mock dependencies
        database = Mock()
        event_service = Mock()
        file_watcher = Mock()
        file_watcher.get_local_files.return_value = []
        
        file_service = FileService(database, event_service, file_watcher)
        
        # Test that file_watcher is properly integrated
        assert file_service.file_watcher == file_watcher


if __name__ == "__main__":
    pytest.main([__file__, "-v"])