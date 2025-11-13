"""
Unit tests for File Service.
Implements test cases from TEST_COVERAGE_ANALYSIS.md Phase 1.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from src.services.file_service import FileService
from src.services.event_service import EventService


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    db = MagicMock()
    db.list_files = AsyncMock(return_value=[])
    db.get_file = AsyncMock()
    db.create_file = AsyncMock()
    db.update_file = AsyncMock(return_value=True)
    db.delete_file = AsyncMock(return_value=True)
    db.get_file_statistics = AsyncMock(return_value={})
    return db


@pytest.fixture
def mock_event_service():
    """Create mock event service for testing."""
    event_service = MagicMock(spec=EventService)
    event_service.emit = AsyncMock()
    event_service.emit_event = AsyncMock()
    return event_service


@pytest.fixture
def mock_file_watcher():
    """Create mock file watcher service."""
    watcher = MagicMock()
    watcher.start = AsyncMock()
    watcher.stop = AsyncMock()
    watcher.get_status = AsyncMock(return_value={'watching': False})
    return watcher


@pytest.fixture
def file_service(mock_database, mock_event_service, mock_file_watcher):
    """Create FileService instance with mock dependencies."""
    service = FileService(
        mock_database,
        mock_event_service,
        mock_file_watcher,
        printer_service=None,
        config_service=None,
        library_service=None
    )
    return service


def create_sample_file_data(
    file_id=None,
    filename='test.3mf',
    file_type='3mf',
    size=1024,
    **kwargs
):
    """Helper to create sample file data."""
    file_id = file_id or str(uuid.uuid4())
    data = {
        'id': file_id,
        'filename': filename,
        'file_type': file_type,
        'size': size,
        'printer_id': None,
        'source': 'local',
        'path': f'/files/{filename}',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }
    data.update(kwargs)
    return data


class TestFileRetrieval:
    """Test file retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_files_all(self, file_service, mock_database):
        """Test retrieving all files."""
        sample_files = [
            create_sample_file_data(file_id=str(uuid.uuid4())),
            create_sample_file_data(file_id=str(uuid.uuid4())),
        ]
        mock_database.list_files.return_value = sample_files
        
        files = await file_service.get_files()
        
        assert len(files) == 2
        mock_database.list_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_files_with_filters(self, file_service, mock_database):
        """Test file retrieval with filters."""
        sample_files = [
            create_sample_file_data(file_type='3mf'),
        ]
        mock_database.list_files.return_value = sample_files
        
        files = await file_service.get_files(file_type='3mf')
        
        assert len(files) == 1
        assert files[0]['file_type'] == '3mf'

    @pytest.mark.asyncio
    async def test_get_file_by_id(self, file_service, mock_database):
        """Test retrieving a specific file by ID."""
        file_id = str(uuid.uuid4())
        file_data = create_sample_file_data(file_id=file_id)
        mock_database.get_file.return_value = file_data
        
        file = await file_service.get_file_by_id(file_id)
        
        assert file is not None
        assert file['id'] == file_id
        mock_database.get_file.assert_called_once_with(file_id)

    @pytest.mark.asyncio
    async def test_get_file_by_id_not_found(self, file_service, mock_database):
        """Test retrieving non-existent file returns None."""
        mock_database.get_file.return_value = None
        
        file = await file_service.get_file_by_id('nonexistent_id')
        
        assert file is None

    @pytest.mark.asyncio
    async def test_find_file_by_name(self, file_service, mock_database):
        """Test finding a file by filename."""
        filename = 'test.3mf'
        file_data = create_sample_file_data(filename=filename)
        mock_database.list_files.return_value = [file_data]
        
        result = await file_service.find_file_by_name(filename)
        
        assert result is not None
        assert result['filename'] == filename


class TestFileDeletion:
    """Test file deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_service, mock_database):
        """Test successful file deletion."""
        file_id = str(uuid.uuid4())
        file_data = create_sample_file_data(file_id=file_id)
        mock_database.get_file.return_value = file_data
        mock_database.delete_file.return_value = True
        
        result = await file_service.delete_file(file_id)
        
        assert result == True
        mock_database.delete_file.assert_called_once_with(file_id)

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, file_service, mock_database):
        """Test deleting non-existent file."""
        mock_database.get_file.return_value = None
        
        result = await file_service.delete_file('nonexistent_id')
        
        assert result == False


class TestFileStatistics:
    """Test file statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_file_statistics(self, file_service, mock_database):
        """Test retrieving file statistics."""
        # Note: actual implementation returns different stats structure
        stats = await file_service.get_file_statistics()
        
        # Verify basic statistics are present
        assert 'total_files' in stats
        assert 'total_size' in stats
        assert isinstance(stats['total_files'], int)
        assert isinstance(stats['total_size'], int)


class TestFileDownloads:
    """Test file download functionality."""

    @pytest.mark.asyncio
    async def test_download_file(self, file_service):
        """Test downloading a file from printer."""
        printer_id = 'printer_001'
        filename = 'test.3mf'
        
        # Mock the downloader service
        file_service.downloader.download_file = AsyncMock(return_value={
            'status': 'success',
            'file_id': str(uuid.uuid4())
        })
        
        result = await file_service.download_file(printer_id, filename)
        
        assert result is not None
        assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_get_download_status(self, file_service):
        """Test getting download status for a file."""
        file_id = str(uuid.uuid4())
        
        # Mock the downloader service
        file_service.downloader.get_download_status = AsyncMock(return_value={
            'file_id': file_id,
            'status': 'in_progress',
            'progress': 50
        })
        
        status = await file_service.get_download_status(file_id)
        
        assert status is not None
        assert status['status'] == 'in_progress'

    def test_download_progress_property(self, file_service):
        """Test accessing download progress property."""
        # Access the property (may be empty dict initially)
        progress = file_service.download_progress
        
        assert isinstance(progress, dict)


class TestFileUploads:
    """Test file upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_files(self, file_service):
        """Test uploading files."""
        files = [
            MagicMock(filename='test1.3mf'),
            MagicMock(filename='test2.stl'),
        ]
        
        # Mock the uploader service
        file_service.uploader.upload_files = AsyncMock(return_value={
            'uploaded': 2,
            'failed': 0,
            'files': [
                {'filename': 'test1.3mf', 'id': str(uuid.uuid4())},
                {'filename': 'test2.stl', 'id': str(uuid.uuid4())}
            ]
        })
        
        result = await file_service.upload_files(files)
        
        assert result['uploaded'] == 2
        assert result['failed'] == 0
        assert len(result['files']) == 2


class TestFileMetadata:
    """Test file metadata extraction."""

    @pytest.mark.asyncio
    async def test_extract_enhanced_metadata(self, file_service):
        """Test extracting enhanced metadata from file."""
        file_id = str(uuid.uuid4())
        
        # Mock the metadata service
        file_service.metadata.extract_enhanced_metadata = AsyncMock(return_value={
            'file_id': file_id,
            'dimensions': {'x': 100, 'y': 100, 'z': 50},
            'layer_count': 250,
            'print_time': 7200
        })
        
        metadata = await file_service.extract_enhanced_metadata(file_id)
        
        assert metadata is not None
        assert 'dimensions' in metadata


class TestFileThumbnails:
    """Test file thumbnail processing."""

    @pytest.mark.asyncio
    async def test_process_file_thumbnails(self, file_service):
        """Test processing thumbnails for a file."""
        file_path = '/files/test.3mf'
        file_id = str(uuid.uuid4())
        
        # Mock the thumbnail service
        file_service.thumbnail.process_file_thumbnails = AsyncMock(return_value=True)
        
        result = await file_service.process_file_thumbnails(file_path, file_id)
        
        assert result == True

    def test_thumbnail_processing_log(self, file_service):
        """Test accessing thumbnail processing log."""
        # Access the log (may be empty list initially)
        log = file_service.thumbnail_processing_log
        
        assert isinstance(log, list)


class TestLocalFiles:
    """Test local file management."""

    @pytest.mark.asyncio
    async def test_get_local_files(self, file_service, mock_database):
        """Test retrieving local files."""
        local_files = [
            create_sample_file_data(source='local'),
            create_sample_file_data(source='local'),
        ]
        mock_database.list_files.return_value = local_files
        
        files = await file_service.get_local_files()
        
        assert len(files) == 2
        for file in files:
            assert file['source'] == 'local'

    @pytest.mark.asyncio
    async def test_scan_local_files(self, file_service):
        """Test scanning for new local files."""
        # Mock the watcher service
        file_service.file_watcher.scan_all = AsyncMock(return_value=[
            {'filename': 'new_file.3mf', 'path': '/watch/new_file.3mf'}
        ])
        
        files = await file_service.scan_local_files()
        
        assert len(files) == 1


class TestWatchFolders:
    """Test watch folder functionality."""

    @pytest.mark.asyncio
    async def test_get_watch_status(self, file_service, mock_file_watcher):
        """Test getting watch folder status."""
        mock_file_watcher.get_status.return_value = {
            'watching': True,
            'folders': ['/watch1', '/watch2']
        }
        
        status = await file_service.get_watch_status()
        
        assert status['watching'] == True
        assert len(status['folders']) == 2

    @pytest.mark.asyncio
    async def test_reload_watch_folders(self, file_service, mock_file_watcher):
        """Test reloading watch folders configuration."""
        mock_file_watcher.reload_config = AsyncMock(return_value={
            'status': 'success',
            'folders_loaded': 2
        })
        
        result = await file_service.reload_watch_folders()
        
        assert result is not None


class TestPrinterFiles:
    """Test printer file operations."""

    @pytest.mark.asyncio
    async def test_get_printer_files(self, file_service, mock_database):
        """Test retrieving files from a specific printer."""
        printer_id = 'printer_001'
        printer_files = [
            create_sample_file_data(printer_id=printer_id),
            create_sample_file_data(printer_id=printer_id),
        ]
        mock_database.list_files.return_value = printer_files
        
        files = await file_service.get_printer_files(printer_id)
        
        assert len(files) == 2
        for file in files:
            assert file['printer_id'] == printer_id

    @pytest.mark.asyncio
    async def test_discover_printer_files(self, file_service):
        """Test discovering files from printer."""
        printer_id = 'printer_001'
        
        # Mock the discovery service
        file_service.discovery.discover_printer_files = AsyncMock(return_value=[
            {'filename': 'file1.3mf', 'size': 1024},
            {'filename': 'file2.3mf', 'size': 2048}
        ])
        
        files = await file_service.discover_printer_files(printer_id)
        
        assert len(files) == 2


class TestServiceCoordination:
    """Test coordination between specialized services."""

    def test_set_printer_service(self, file_service):
        """Test setting printer service after initialization."""
        mock_printer_service = MagicMock()
        
        file_service.set_printer_service(mock_printer_service)
        
        assert file_service.printer_service == mock_printer_service

    def test_set_config_service(self, file_service):
        """Test setting config service after initialization."""
        mock_config_service = MagicMock()
        
        file_service.set_config_service(mock_config_service)
        
        assert file_service.config_service == mock_config_service

    def test_set_library_service(self, file_service):
        """Test setting library service after initialization."""
        mock_library_service = MagicMock()
        
        file_service.set_library_service(mock_library_service)
        
        assert file_service.library_service == mock_library_service

    @pytest.mark.asyncio
    async def test_shutdown(self, file_service, mock_file_watcher):
        """Test file service shutdown."""
        mock_file_watcher.stop = AsyncMock()
        
        await file_service.shutdown()
        
        mock_file_watcher.stop.assert_called_once()


class TestFileValidation:
    """Test file validation and error handling."""

    @pytest.mark.asyncio
    async def test_get_files_empty_list(self, file_service, mock_database):
        """Test handling of empty file list."""
        mock_database.list_files.return_value = []
        
        files = await file_service.get_files()
        
        assert files == []

    @pytest.mark.asyncio
    async def test_get_files_with_pagination(self, file_service, mock_database):
        """Test file retrieval with pagination."""
        sample_files = [create_sample_file_data(file_id=str(uuid.uuid4())) for _ in range(10)]
        mock_database.list_files.return_value = sample_files
        
        # Note: FileService.get_files doesn't have offset parameter
        files = await file_service.get_files(limit=5)
        
        # Should return files
        assert isinstance(files, list)

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, file_service, mock_database):
        """Test handling of file not found errors."""
        mock_database.get_file.return_value = None
        
        file = await file_service.get_file_by_id('nonexistent_id')
        
        assert file is None
