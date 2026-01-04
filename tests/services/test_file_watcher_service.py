"""
Unit tests for FileWatcherService.
Tests file system monitoring, event handling, and watch folder management.

Sprint 2 Phase 2 - Feature Service Test Coverage.
"""
import pytest
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.file_watcher_service import (
    FileWatcherService, PrintFileHandler, LocalFile
)


class TestPrintFileHandler:
    """Test PrintFileHandler file filtering and event handling."""

    def test_supported_extensions(self):
        """Test supported file extensions are defined."""
        expected = {'.stl', '.3mf', '.gcode', '.obj', '.ply'}
        assert PrintFileHandler.SUPPORTED_EXTENSIONS == expected

    def test_should_process_file_valid_stl(self):
        """Test STL files are processed."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/model.stl") is True

    def test_should_process_file_valid_3mf(self):
        """Test 3MF files are processed."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/model.3mf") is True

    def test_should_process_file_valid_gcode(self):
        """Test GCODE files are processed."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/model.gcode") is True

    def test_should_process_file_valid_obj(self):
        """Test OBJ files are processed."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/model.obj") is True

    def test_should_process_file_valid_ply(self):
        """Test PLY files are processed."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/model.ply") is True

    def test_should_process_file_uppercase_extension(self):
        """Test uppercase extensions are handled."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/MODEL.STL") is True

    def test_should_process_file_invalid_extension(self):
        """Test unsupported extensions are rejected."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/document.pdf") is False

    def test_should_process_file_hidden_file(self):
        """Test hidden files are ignored."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/.hidden.stl") is False

    def test_should_process_file_temp_file(self):
        """Test temp files are ignored."""
        handler = PrintFileHandler(MagicMock())
        assert handler.should_process_file("/path/to/model.stl.tmp") is False

    def test_debounce_event_first_event(self):
        """Test first event is not debounced."""
        handler = PrintFileHandler(MagicMock())
        result = handler._debounce_event("/path/to/model.stl")
        assert result is True

    def test_debounce_event_rapid_second_event(self):
        """Test rapid second event is debounced."""
        handler = PrintFileHandler(MagicMock())
        handler._debounce_event("/path/to/model.stl")
        result = handler._debounce_event("/path/to/model.stl")
        assert result is False

    def test_debounce_event_different_files(self):
        """Test different files are not debounced."""
        handler = PrintFileHandler(MagicMock())
        handler._debounce_event("/path/to/model1.stl")
        result = handler._debounce_event("/path/to/model2.stl")
        assert result is True


class TestLocalFile:
    """Test LocalFile dataclass."""

    def test_local_file_creation(self):
        """Test LocalFile creation with all fields."""
        local_file = LocalFile(
            file_id="local_123456",
            filename="test.stl",
            file_path="/path/to/test.stl",
            file_size=1024,
            file_type=".stl",
            modified_time=datetime.now(),
            watch_folder_path="/path/to",
            relative_path="test.stl"
        )

        assert local_file.file_id == "local_123456"
        assert local_file.filename == "test.stl"
        assert local_file.file_size == 1024
        assert local_file.file_type == ".stl"


class TestFileWatcherServiceInitialization:
    """Test FileWatcherService initialization."""

    def test_initialization_default(self):
        """Test FileWatcherService initializes with defaults."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)

        assert service.config_service is mock_config
        assert service.event_service is mock_event
        assert service.library_service is None
        assert service._is_running is False
        assert len(service._watched_folders) == 0
        assert len(service._local_files) == 0

    def test_initialization_with_library(self):
        """Test FileWatcherService initializes with library service."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_library = MagicMock()

        service = FileWatcherService(mock_config, mock_event, mock_library)

        assert service.library_service is mock_library

    def test_file_handler_initialized(self):
        """Test PrintFileHandler is created on init."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)

        assert service._file_handler is not None
        assert isinstance(service._file_handler, PrintFileHandler)


class TestFileWatcherServiceStartStop:
    """Test FileWatcherService start and stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_when_disabled(self):
        """Test start does nothing when watch folders disabled."""
        mock_config = MagicMock()
        mock_config.is_watch_folders_enabled.return_value = False
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        await service.start()

        assert service._is_running is False

    @pytest.mark.asyncio
    async def test_start_when_already_running(self):
        """Test start logs warning when already running."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._is_running = True

        with patch('src.services.file_watcher_service.logger') as mock_logger:
            await service.start()
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test stop does nothing when not running."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)

        await service.stop()  # Should not raise

        assert service._is_running is False

    @pytest.mark.asyncio
    async def test_stop_clears_watched_folders(self):
        """Test stop clears watched folders."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._is_running = True
        service._watched_folders = {"/path/to/folder": {}}

        await service.stop()

        assert len(service._watched_folders) == 0
        assert service._is_running is False


class TestFileWatcherServiceWatchFolders:
    """Test watch folder management."""

    @pytest.mark.asyncio
    async def test_add_watch_folder_invalid(self):
        """Test adding invalid watch folder."""
        mock_config = MagicMock()
        mock_config.validate_watch_folder.return_value = {
            "valid": False,
            "error": "Folder does not exist"
        }
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)

        await service._add_watch_folder("/nonexistent/path")

        assert len(service._watched_folders) == 0

    @pytest.mark.asyncio
    async def test_add_watch_folder_valid(self):
        """Test adding valid watch folder in fallback mode."""
        mock_config = MagicMock()
        mock_config.validate_watch_folder.return_value = {"valid": True}
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._observer = None  # Fallback mode

        with tempfile.TemporaryDirectory() as tmpdir:
            await service._add_watch_folder(tmpdir)

            assert tmpdir in service._watched_folders

    @pytest.mark.asyncio
    async def test_add_watch_folder_stores_recursive_flag(self):
        """Test watch folder stores recursive flag."""
        mock_config = MagicMock()
        mock_config.validate_watch_folder.return_value = {"valid": True}
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._observer = None

        with tempfile.TemporaryDirectory() as tmpdir:
            await service._add_watch_folder(tmpdir, recursive=True)

            folder_info = service._watched_folders[tmpdir]
            assert folder_info['recursive'] is True


class TestFileWatcherServiceFileHandling:
    """Test file event handling."""

    @pytest.mark.asyncio
    async def test_handle_file_created(self):
        """Test file creation handling."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up watch folder
            service._watched_folders[tmpdir] = {
                'watch': None,
                'path': Path(tmpdir),
                'recursive': True
            }

            # Create a test file
            test_file = Path(tmpdir) / "test.stl"
            test_file.write_bytes(b"test content")

            await service._handle_file_created(str(test_file))

            # File should be in local files
            assert len(service._local_files) == 1

    @pytest.mark.asyncio
    async def test_handle_file_deleted(self):
        """Test file deletion handling."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        # Add a file to track
        local_file = LocalFile(
            file_id="local_123",
            filename="test.stl",
            file_path="/path/to/test.stl",
            file_size=1024,
            file_type=".stl",
            modified_time=datetime.now(),
            watch_folder_path="/path/to",
            relative_path="test.stl"
        )
        service._local_files["local_123"] = local_file

        await service._handle_file_deleted("/path/to/test.stl")

        assert "local_123" not in service._local_files

    @pytest.mark.asyncio
    async def test_handle_file_modified(self):
        """Test file modification handling."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.stl"
            test_file.write_bytes(b"test content")

            # Add to tracking
            local_file = LocalFile(
                file_id="local_123",
                filename="test.stl",
                file_path=str(test_file),
                file_size=12,
                file_type=".stl",
                modified_time=datetime.now(),
                watch_folder_path=tmpdir,
                relative_path="test.stl"
            )
            service._local_files["local_123"] = local_file

            # Modify file
            test_file.write_bytes(b"updated content")

            await service._handle_file_modified(str(test_file))

            # Size should be updated
            assert service._local_files["local_123"].file_size == 15

    @pytest.mark.asyncio
    async def test_handle_file_moved(self):
        """Test file move handling."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up watch folder
            service._watched_folders[tmpdir] = {
                'watch': None,
                'path': Path(tmpdir),
                'recursive': True
            }

            old_path = f"{tmpdir}/old_name.stl"
            new_path = f"{tmpdir}/new_name.stl"

            # Add to tracking with old path
            local_file = LocalFile(
                file_id="local_123",
                filename="old_name.stl",
                file_path=old_path,
                file_size=1024,
                file_type=".stl",
                modified_time=datetime.now(),
                watch_folder_path=tmpdir,
                relative_path="old_name.stl"
            )
            service._local_files["local_123"] = local_file

            await service._handle_file_moved(old_path, new_path)

            # Path should be updated
            assert service._local_files["local_123"].file_path == new_path
            assert service._local_files["local_123"].filename == "new_name.stl"


class TestFileWatcherServiceStatus:
    """Test status reporting."""

    def test_get_watch_status(self):
        """Test watch status includes all fields."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._is_running = True
        service._watched_folders = {"/path/to/folder": {}}
        service._local_files = {"file1": MagicMock(), "file2": MagicMock()}

        status = service.get_watch_status()

        assert status['is_running'] is True
        assert status['watched_folders'] == ["/path/to/folder"]
        assert status['local_files_count'] == 2
        assert 'supported_extensions' in status

    def test_get_local_files(self):
        """Test getting list of local files."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)

        local_file = LocalFile(
            file_id="local_123",
            filename="test.stl",
            file_path="/path/to/test.stl",
            file_size=1024,
            file_type=".stl",
            modified_time=datetime.now(),
            watch_folder_path="/path/to",
            relative_path="test.stl"
        )
        service._local_files["local_123"] = local_file

        files = service.get_local_files()

        assert len(files) == 1
        assert files[0]['id'] == "local_123"
        assert files[0]['filename'] == "test.stl"
        assert files[0]['status'] == 'local'
        assert files[0]['source'] == 'local_watch'


class TestFileWatcherServiceEventEmission:
    """Test event emission."""

    @pytest.mark.asyncio
    async def test_emit_file_event(self):
        """Test file event emission."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        local_file = LocalFile(
            file_id="local_123",
            filename="test.stl",
            file_path="/path/to/test.stl",
            file_size=1024,
            file_type=".stl",
            modified_time=datetime.now(),
            watch_folder_path="/path/to",
            relative_path="test.stl"
        )

        await service._emit_file_event('file_discovered', local_file)

        mock_event.emit_event.assert_called_once()
        call_args = mock_event.emit_event.call_args
        assert call_args[0][0] == 'file_watcher'
        assert call_args[0][1]['event_type'] == 'file_discovered'
        assert call_args[0][1]['filename'] == 'test.stl'

    @pytest.mark.asyncio
    async def test_emit_file_event_error_handling(self):
        """Test event emission error handling."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock(side_effect=Exception("Event error"))

        service = FileWatcherService(mock_config, mock_event)

        local_file = LocalFile(
            file_id="local_123",
            filename="test.stl",
            file_path="/path/to/test.stl",
            file_size=1024,
            file_type=".stl",
            modified_time=datetime.now(),
            watch_folder_path="/path/to",
            relative_path="test.stl"
        )

        # Should not raise
        await service._emit_file_event('file_discovered', local_file)


class TestFileWatcherServiceFolderLookup:
    """Test watch folder lookup."""

    def test_find_watch_folder_for_file_found(self):
        """Test finding watch folder for file."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._watched_folders = {
            "/home/user/models": {},
            "/home/user/prints": {}
        }

        result = service._find_watch_folder_for_file("/home/user/models/test.stl")

        assert result == "/home/user/models"

    def test_find_watch_folder_for_file_nested(self):
        """Test finding watch folder for nested file."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._watched_folders = {
            "/home/user/models": {}
        }

        result = service._find_watch_folder_for_file("/home/user/models/subdir/test.stl")

        assert result == "/home/user/models"

    def test_find_watch_folder_for_file_not_found(self):
        """Test file not in any watch folder."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._watched_folders = {
            "/home/user/models": {}
        }

        result = service._find_watch_folder_for_file("/other/path/test.stl")

        assert result is None


class TestFileWatcherServiceReload:
    """Test configuration reload."""

    @pytest.mark.asyncio
    async def test_reload_when_not_running(self):
        """Test reload does nothing when not running."""
        mock_config = MagicMock()
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)

        with patch('src.services.file_watcher_service.logger') as mock_logger:
            await service.reload_watch_folders()
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_reload_restarts_service(self):
        """Test reload stops and starts service."""
        mock_config = MagicMock()
        mock_config.is_watch_folders_enabled.return_value = False
        mock_event = MagicMock()

        service = FileWatcherService(mock_config, mock_event)
        service._is_running = True

        with patch.object(service, 'stop', new_callable=AsyncMock) as mock_stop:
            with patch.object(service, 'start', new_callable=AsyncMock) as mock_start:
                await service.reload_watch_folders()

                mock_stop.assert_called_once()
                mock_start.assert_called_once()


class TestFileWatcherServiceScan:
    """Test folder scanning."""

    @pytest.mark.asyncio
    async def test_scan_folder_recursive(self):
        """Test recursive folder scanning."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            # Create files
            (Path(tmpdir) / "root.stl").write_bytes(b"root")
            (subdir / "nested.stl").write_bytes(b"nested")

            service._watched_folders[tmpdir] = {
                'watch': None,
                'path': Path(tmpdir),
                'recursive': True
            }

            await service._scan_folder(Path(tmpdir), recursive=True)

            # Should find both files
            assert len(service._local_files) == 2

    @pytest.mark.asyncio
    async def test_scan_folder_non_recursive(self):
        """Test non-recursive folder scanning."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        service = FileWatcherService(mock_config, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            # Create files
            (Path(tmpdir) / "root.stl").write_bytes(b"root")
            (subdir / "nested.stl").write_bytes(b"nested")

            service._watched_folders[tmpdir] = {
                'watch': None,
                'path': Path(tmpdir),
                'recursive': False
            }

            await service._scan_folder(Path(tmpdir), recursive=False)

            # Should only find root file
            assert len(service._local_files) == 1


class TestFileWatcherServiceLibraryIntegration:
    """Test library service integration."""

    @pytest.mark.asyncio
    async def test_process_file_with_library_new_file(self):
        """Test new file is added to library."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        mock_library = MagicMock()
        mock_library.enabled = True
        mock_library.calculate_checksum = AsyncMock(return_value="abc123")
        mock_library.get_file_by_checksum = AsyncMock(return_value=None)
        mock_library.add_file_to_library = AsyncMock()

        service = FileWatcherService(mock_config, mock_event, mock_library)

        with tempfile.TemporaryDirectory() as tmpdir:
            service._watched_folders[tmpdir] = {
                'watch': None,
                'path': Path(tmpdir),
                'recursive': True
            }

            test_file = Path(tmpdir) / "new.stl"
            test_file.write_bytes(b"new file content")

            await service._process_discovered_file(str(test_file))

            mock_library.add_file_to_library.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_file_with_library_duplicate(self):
        """Test duplicate file adds source reference."""
        mock_config = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()

        mock_library = MagicMock()
        mock_library.enabled = True
        mock_library.calculate_checksum = AsyncMock(return_value="abc123")
        mock_library.get_file_by_checksum = AsyncMock(return_value={'filename': 'existing.stl'})
        mock_library.add_file_source = AsyncMock()

        service = FileWatcherService(mock_config, mock_event, mock_library)

        with tempfile.TemporaryDirectory() as tmpdir:
            service._watched_folders[tmpdir] = {
                'watch': None,
                'path': Path(tmpdir),
                'recursive': True
            }

            test_file = Path(tmpdir) / "duplicate.stl"
            test_file.write_bytes(b"duplicate content")

            await service._process_discovered_file(str(test_file))

            mock_library.add_file_source.assert_called_once()
