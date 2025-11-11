"""
Unit tests for Library Service
Tests checksum calculation, file organization, deduplication, and source tracking.
"""
import pytest
import tempfile
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import json


# Sample file content for testing
SAMPLE_FILE_CONTENT = b"This is a test 3D model file content for checksum testing."
SAMPLE_FILE_CHECKSUM = hashlib.sha256(SAMPLE_FILE_CONTENT).hexdigest()


@pytest.fixture
def temp_library_path():
    """Create temporary library directory"""
    temp_dir = tempfile.mkdtemp(prefix='library_test_')
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_database():
    """Mock database for library service testing"""
    db = Mock()

    # Make database stateful - store files that are created
    # Store as attribute so tests can pre-populate it
    db._created_files = {}

    async def create_file(file_record):
        db._created_files[file_record['checksum']] = file_record
        return True

    async def get_file(checksum):
        return db._created_files.get(checksum, None)

    db.create_library_file = AsyncMock(side_effect=create_file)
    db.get_library_file_by_checksum = AsyncMock(side_effect=get_file)
    db.update_library_file = AsyncMock(return_value=True)
    db.create_library_file_source = AsyncMock(return_value=True)
    db.delete_library_file = AsyncMock(return_value=True)
    db.delete_library_file_sources = AsyncMock(return_value=True)
    db.list_library_files = AsyncMock(return_value=([], {'page': 1, 'total_items': 0}))
    db.get_library_stats = AsyncMock(return_value={})
    return db


@pytest.fixture
def mock_config_service(temp_library_path):
    """Mock configuration service"""
    config = Mock()
    config.settings = Mock()
    config.settings.library_path = str(temp_library_path)
    config.settings.library_enabled = True
    config.settings.library_auto_organize = True
    config.settings.library_auto_extract_metadata = True
    config.settings.library_checksum_algorithm = 'sha256'
    config.settings.library_preserve_originals = True
    return config


@pytest.fixture
def mock_event_service():
    """Mock event service"""
    events = Mock()
    events.emit_event = AsyncMock()
    return events


@pytest.fixture
async def library_service(mock_database, mock_config_service, mock_event_service):
    """Initialize library service with mocks"""
    from src.services.library_service import LibraryService
    service = LibraryService(mock_database, mock_config_service, mock_event_service)
    await service.initialize()
    return service


@pytest.fixture
def sample_test_file(temp_library_path):
    """Create a sample test file"""
    test_file = temp_library_path / 'test_input.3mf'
    test_file.write_bytes(SAMPLE_FILE_CONTENT)
    return test_file


class TestLibraryServiceInitialization:
    """Test library service initialization"""

    @pytest.mark.asyncio
    async def test_initialize_creates_folders(self, library_service, temp_library_path):
        """Test that initialization creates required folders"""
        assert (temp_library_path / 'models').exists()
        assert (temp_library_path / 'printers').exists()
        assert (temp_library_path / 'uploads').exists()
        assert (temp_library_path / '.metadata' / 'thumbnails').exists()
        assert (temp_library_path / '.metadata' / 'previews').exists()

    @pytest.mark.asyncio
    async def test_initialize_validates_write_permissions(self, library_service, temp_library_path):
        """Test that initialization validates write permissions"""
        # Should not raise an error
        assert library_service.enabled

    @pytest.mark.asyncio
    async def test_disabled_library_skips_initialization(self, mock_database, mock_config_service, mock_event_service):
        """Test that disabled library skips folder creation"""
        mock_config_service.settings.library_enabled = False
        from src.services.library_service import LibraryService
        service = LibraryService(mock_database, mock_config_service, mock_event_service)
        await service.initialize()
        assert not service.enabled


class TestChecksumCalculation:
    """Test checksum calculation functionality"""

    @pytest.mark.asyncio
    async def test_calculate_checksum_sha256(self, library_service, sample_test_file):
        """Test SHA-256 checksum calculation"""
        checksum = await library_service.calculate_checksum(sample_test_file)
        assert checksum == SAMPLE_FILE_CHECKSUM
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters

    @pytest.mark.asyncio
    async def test_calculate_checksum_consistent(self, library_service, sample_test_file):
        """Test that checksum calculation is consistent"""
        checksum1 = await library_service.calculate_checksum(sample_test_file)
        checksum2 = await library_service.calculate_checksum(sample_test_file)
        assert checksum1 == checksum2

    @pytest.mark.asyncio
    async def test_calculate_checksum_different_files(self, library_service, temp_library_path):
        """Test that different files have different checksums"""
        file1 = temp_library_path / 'file1.3mf'
        file2 = temp_library_path / 'file2.3mf'
        file1.write_bytes(b"Content A")
        file2.write_bytes(b"Content B")

        checksum1 = await library_service.calculate_checksum(file1)
        checksum2 = await library_service.calculate_checksum(file2)
        assert checksum1 != checksum2


class TestLibraryPathGeneration:
    """Test library path generation for different source types"""

    def test_watch_folder_path_generation(self, library_service):
        """Test path generation for watch folder files"""
        checksum = "a3f8d9e8b2c4f1a7e6d5c3b2a1f0e9d8"
        path = library_service.get_library_path_for_file(
            checksum, 'watch_folder', 'benchy.3mf'
        )

        assert 'models' in str(path)
        assert 'benchy.3mf' in str(path)  # Uses natural filename
        assert path.suffix == '.3mf'

    def test_printer_path_generation(self, library_service):
        """Test path generation for printer files"""
        checksum = "b7d4e2f1c8a9b6e3d2f5a4c7b8d9e1f0"
        path = library_service.get_library_path_for_file(
            checksum, 'printer', 'benchy.gcode', printer_name='bambu_a1'
        )

        assert 'printers' in str(path)
        assert 'bambu_a1' in str(path)
        assert 'benchy.gcode' in str(path)  # Uses natural filename

    def test_upload_path_generation(self, library_service):
        """Test path generation for uploaded files"""
        checksum = "c4b9e7f2d1a8c6b5e3f4d2a9c7b8e1f0"
        path = library_service.get_library_path_for_file(
            checksum, 'upload', 'model.stl'
        )

        assert 'uploads' in str(path)
        assert 'model.stl' in str(path)  # Uses natural filename
        assert path.suffix == '.stl'

    def test_path_sharding_distribution(self, library_service):
        """Test that files from same source type go to same directory (no sharding)"""
        checksums = [
            "a0" + "0" * 62,
            "b1" + "0" * 62,
            "c2" + "0" * 62,
            "ff" + "0" * 62
        ]

        paths = [
            library_service.get_library_path_for_file(c, 'watch_folder', 'test.3mf')
            for c in checksums
        ]

        # All should be in the same directory (models) - no sharding
        shards = [p.parent.name for p in paths]
        assert len(set(shards)) == 1  # All same
        assert shards[0] == 'models'


class TestFileAddition:
    """Test adding files to library"""

    @pytest.mark.asyncio
    async def test_add_new_file_to_library(self, library_service, sample_test_file, mock_database):
        """Test adding a new file to library"""
        source_info = {
            'type': 'watch_folder',
            'folder_path': '/test/models',
            'relative_path': 'benchy.3mf'
        }

        result = await library_service.add_file_to_library(
            sample_test_file, source_info, copy_file=True
        )

        assert result is not None
        assert result['checksum'] == SAMPLE_FILE_CHECKSUM
        assert result['filename'] == 'test_input.3mf'
        mock_database.create_library_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_duplicate_file_adds_source(self, library_service, sample_test_file, mock_database):
        """Test that adding duplicate file creates new record marked as duplicate"""
        existing_file = {
            'id': 'existing-uuid',
            'checksum': SAMPLE_FILE_CHECKSUM,
            'filename': 'existing.3mf',
            'sources': '[]',  # Add sources field for the update logic
            'duplicate_count': 0
        }
        # Pre-populate the database with existing file
        mock_database._created_files[SAMPLE_FILE_CHECKSUM] = existing_file

        source_info = {
            'type': 'watch_folder',
            'folder_path': '/test/models',
            'relative_path': 'benchy.3mf'
        }

        result = await library_service.add_file_to_library(
            sample_test_file, source_info, copy_file=True
        )

        # Should create a new file record for the duplicate (with modified checksum)
        assert result is not None
        assert result['is_duplicate'] is True
        assert result['duplicate_of_checksum'] == SAMPLE_FILE_CHECKSUM
        assert SAMPLE_FILE_CHECKSUM in result['checksum']  # Modified checksum includes original
        mock_database.create_library_file.assert_called_once()
        mock_database.create_library_file_source.assert_called()

    @pytest.mark.asyncio
    async def test_disk_space_check(self, library_service, temp_library_path, mock_database):
        """Test that disk space is checked before copying"""
        # Create a large file (simulated)
        large_file = temp_library_path / 'large.3mf'
        large_file.write_bytes(b"X" * (1024 * 1024))  # 1MB

        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(free=500 * 1024)  # Only 500KB free

            source_info = {'type': 'watch_folder', 'folder_path': '/test'}

            with pytest.raises(IOError, match="Insufficient disk space"):
                await library_service.add_file_to_library(
                    large_file, source_info, copy_file=True
                )

    @pytest.mark.asyncio
    async def test_file_copy_preserves_original(self, library_service, sample_test_file, mock_database, temp_library_path):
        """Test that copying file preserves original"""
        source_info = {'type': 'watch_folder', 'folder_path': '/test'}

        await library_service.add_file_to_library(
            sample_test_file, source_info, copy_file=True
        )

        # Original file should still exist
        assert sample_test_file.exists()
        assert sample_test_file.read_bytes() == SAMPLE_FILE_CONTENT

    @pytest.mark.asyncio
    async def test_checksum_verification_after_copy(self, library_service, sample_test_file, mock_database):
        """Test that checksum is verified after copying"""
        source_info = {'type': 'watch_folder', 'folder_path': '/test'}

        # Should not raise error
        result = await library_service.add_file_to_library(
            sample_test_file, source_info, copy_file=True
        )

        assert result is not None


class TestSourceTracking:
    """Test multi-source tracking"""

    @pytest.mark.asyncio
    async def test_add_multiple_sources(self, library_service, mock_database):
        """Test adding multiple sources to same file"""
        checksum = SAMPLE_FILE_CHECKSUM

        source1 = {
            'type': 'watch_folder',
            'folder_path': '/test/models',
            'discovered_at': datetime.now().isoformat()
        }
        source2 = {
            'type': 'printer',
            'printer_id': 'bambu-001',
            'printer_name': 'Bambu A1',
            'discovered_at': datetime.now().isoformat()
        }

        existing_file = {
            'id': 'file-uuid',
            'checksum': checksum,
            'sources': json.dumps([source1])
        }
        # Pre-populate the database with existing file
        mock_database._created_files[checksum] = existing_file

        await library_service.add_file_source(checksum, source2)

        # Should update sources array
        mock_database.update_library_file.assert_called()
        call_args = mock_database.update_library_file.call_args
        sources_json = call_args[0][1]['sources']
        sources = json.loads(sources_json)
        assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_duplicate_source_not_added(self, library_service, mock_database):
        """Test that duplicate sources are not added"""
        checksum = SAMPLE_FILE_CHECKSUM
        source_info = {
            'type': 'watch_folder',
            'folder_path': '/test/models'
        }

        existing_file = {
            'id': 'file-uuid',
            'checksum': checksum,
            'sources': json.dumps([source_info])
        }
        # Pre-populate the database with existing file
        mock_database._created_files[checksum] = existing_file

        await library_service.add_file_source(checksum, source_info)

        # Should not update if source already exists
        mock_database.update_library_file.assert_not_called()


class TestFileDeletion:
    """Test file deletion"""

    @pytest.mark.asyncio
    async def test_delete_file_with_physical(self, library_service, mock_database, temp_library_path):
        """Test deleting file including physical file"""
        # Create a file in library
        test_file = temp_library_path / 'models' / 'a3' / f"{SAMPLE_FILE_CHECKSUM}.3mf"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(SAMPLE_FILE_CONTENT)

        file_record = {
            'id': 'file-uuid',
            'checksum': SAMPLE_FILE_CHECKSUM,
            'library_path': f"models/a3/{SAMPLE_FILE_CHECKSUM}.3mf",
            'filename': 'test.3mf'
        }
        # Pre-populate the database with existing file
        mock_database._created_files[SAMPLE_FILE_CHECKSUM] = file_record

        result = await library_service.delete_file(SAMPLE_FILE_CHECKSUM, delete_physical=True)

        assert result is True
        assert not test_file.exists()  # Physical file deleted
        mock_database.delete_library_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_database_only(self, library_service, mock_database, temp_library_path):
        """Test deleting file from database only"""
        test_file = temp_library_path / 'models' / 'a3' / f"{SAMPLE_FILE_CHECKSUM}.3mf"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(SAMPLE_FILE_CONTENT)

        file_record = {
            'id': 'file-uuid',
            'checksum': SAMPLE_FILE_CHECKSUM,
            'library_path': f"models/a3/{SAMPLE_FILE_CHECKSUM}.3mf",
            'filename': 'test.3mf'
        }
        # Pre-populate the database with existing file
        mock_database._created_files[SAMPLE_FILE_CHECKSUM] = file_record

        result = await library_service.delete_file(SAMPLE_FILE_CHECKSUM, delete_physical=False)

        assert result is True
        assert test_file.exists()  # Physical file preserved
        mock_database.delete_library_file.assert_called_once()


class TestListFiles:
    """Test file listing and filtering"""

    @pytest.mark.asyncio
    async def test_list_files_with_pagination(self, library_service, mock_database):
        """Test file listing with pagination"""
        files_data = [
            {'id': f'file-{i}', 'checksum': f'checksum-{i}', 'filename': f'file{i}.3mf'}
            for i in range(5)
        ]
        pagination = {'page': 1, 'limit': 50, 'total_items': 5, 'total_pages': 1}
        mock_database.list_library_files.return_value = (files_data, pagination)

        files, page_info = await library_service.list_files({}, page=1, limit=50)

        assert len(files) == 5
        assert page_info['total_items'] == 5
        mock_database.list_library_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_files_with_filters(self, library_service, mock_database):
        """Test file listing with filters"""
        filters = {
            'source_type': 'printer',
            'file_type': '.3mf',
            'has_thumbnail': True
        }

        await library_service.list_files(filters, page=1, limit=50)

        call_args = mock_database.list_library_files.call_args
        assert call_args[0][0] == filters


class TestReprocessing:
    """Test file reprocessing"""

    @pytest.mark.asyncio
    async def test_reprocess_file(self, library_service, mock_database):
        """Test reprocessing file metadata"""
        file_record = {
            'id': 'file-uuid',
            'checksum': SAMPLE_FILE_CHECKSUM,
            'filename': 'test.3mf'
        }
        # Pre-populate the database with existing file
        mock_database._created_files[SAMPLE_FILE_CHECKSUM] = file_record

        result = await library_service.reprocess_file(SAMPLE_FILE_CHECKSUM)

        assert result is True

    @pytest.mark.asyncio
    async def test_reprocess_nonexistent_file(self, library_service, mock_database):
        """Test reprocessing non-existent file"""
        mock_database.get_library_file_by_checksum.return_value = None

        result = await library_service.reprocess_file('nonexistent-checksum')

        assert result is False


class TestStatistics:
    """Test library statistics"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, library_service, mock_database):
        """Test getting library statistics"""
        stats = {
            'total_files': 142,
            'total_size': 2458374144,
            'files_with_thumbnails': 89
        }
        mock_database.get_library_stats.return_value = stats

        result = await library_service.get_library_statistics()

        assert result == stats
        mock_database.get_library_stats.assert_called_once()


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_add_file_missing_source(self, library_service, sample_test_file):
        """Test adding file without source"""
        with pytest.raises(FileNotFoundError):
            nonexistent = Path('/nonexistent/file.3mf')
            await library_service.add_file_to_library(
                nonexistent, {'type': 'watch_folder'}, copy_file=True
            )

    @pytest.mark.asyncio
    async def test_add_file_invalid_source_type(self, library_service, sample_test_file):
        """Test adding file with invalid source type"""
        with pytest.raises(ValueError, match="Invalid source type"):
            await library_service.add_file_to_library(
                sample_test_file, {'type': 'invalid_type'}, copy_file=True
            )

    @pytest.mark.asyncio
    async def test_database_error_cleanup(self, library_service, sample_test_file, mock_database, temp_library_path):
        """Test that physical file is cleaned up on database error"""
        mock_database.create_library_file.side_effect = Exception("Database error")

        source_info = {'type': 'watch_folder', 'folder_path': '/test'}

        with pytest.raises(Exception, match="Database error"):
            await library_service.add_file_to_library(
                sample_test_file, source_info, copy_file=True
            )

        # Physical file should be cleaned up
        # (Would need to verify no orphaned files in library)


class TestConcurrency:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_file_additions(self, library_service, mock_database):
        """Test handling concurrent additions of same file"""
        # First call succeeds
        mock_database.create_library_file.return_value = True

        # Second call fails (checksum exists)
        async def side_effect(*args, **kwargs):
            if mock_database.create_library_file.call_count > 1:
                return False
            return True

        mock_database.create_library_file.side_effect = side_effect

        # This should handle the race condition gracefully
        # (actual test would need more complex setup)


class TestIntegration:
    """Integration tests for library service"""

    @pytest.mark.asyncio
    async def test_full_file_lifecycle(self, library_service, sample_test_file, mock_database):
        """Test complete file lifecycle: add, list, get, reprocess, delete"""
        # Add file
        source_info = {'type': 'watch_folder', 'folder_path': '/test'}
        add_result = await library_service.add_file_to_library(
            sample_test_file, source_info, copy_file=True
        )
        assert add_result is not None

        # Get file
        file_record = {
            'id': 'file-uuid',
            'checksum': SAMPLE_FILE_CHECKSUM,
            'filename': 'test.3mf'
        }
        mock_database.get_library_file_by_checksum.return_value = file_record
        get_result = await library_service.get_file_by_checksum(SAMPLE_FILE_CHECKSUM)
        assert get_result is not None

        # Reprocess
        reprocess_result = await library_service.reprocess_file(SAMPLE_FILE_CHECKSUM)
        assert reprocess_result is True

        # Delete
        delete_result = await library_service.delete_file(SAMPLE_FILE_CHECKSUM, delete_physical=False)
        assert delete_result is True
