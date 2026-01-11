"""
Unit tests for FileUploadService.
Tests file validation, upload processing, and library integration.

Sprint 2 Phase 2 - Feature Service Test Coverage.
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from unittest.mock import MagicMock, AsyncMock, patch, mock_open

from src.services.file_upload_service import FileUploadService


class MockUploadFile:
    """Mock FastAPI UploadFile for testing."""

    def __init__(self, filename: str, content: bytes, size: int = None):
        self.filename = filename
        self._content = content
        self.size = size or len(content)

    async def read(self):
        return self._content


class MockSettings:
    """Mock settings for testing."""

    def __init__(self):
        self.enable_upload = True
        self.allowed_upload_extensions_list = ['.stl', '.3mf', '.gcode', '.obj']
        self.max_upload_size_mb = 100
        self.downloads_path = "/tmp/downloads"


class TestFileUploadServiceInitialization:
    """Test FileUploadService initialization."""

    def test_initialization_with_required_services(self):
        """Test initialization with required services."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        assert service.database is mock_db
        assert service.event_service is mock_event
        assert service.thumbnail_service is None
        assert service.metadata_service is None
        assert service.library_service is None

    def test_initialization_with_optional_services(self):
        """Test initialization with all optional services."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_thumbnail = MagicMock()
        mock_metadata = MagicMock()
        mock_library = MagicMock()
        mock_usage = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(
                    mock_db, mock_event,
                    thumbnail_service=mock_thumbnail,
                    metadata_service=mock_metadata,
                    library_service=mock_library,
                    usage_stats_service=mock_usage
                )

        assert service.thumbnail_service is mock_thumbnail
        assert service.metadata_service is mock_metadata
        assert service.library_service is mock_library
        assert service.usage_stats_service is mock_usage


class TestFileValidation:
    """Test file validation logic."""

    def test_validate_file_uploads_disabled(self):
        """Test validation fails when uploads disabled."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        settings = MockSettings()
        settings.enable_upload = False

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = service.validate_file("test.stl", 1024)

        assert result['valid'] is False
        assert "disabled" in result['error'].lower()

    def test_validate_file_valid_extension(self):
        """Test validation passes for valid extension."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = service.validate_file("model.stl", 1024)

        assert result['valid'] is True
        assert result['file_type'] == 'stl'

    def test_validate_file_invalid_extension(self):
        """Test validation fails for invalid extension."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = service.validate_file("document.pdf", 1024)

        assert result['valid'] is False
        assert ".pdf" in result['error']

    def test_validate_file_too_large(self):
        """Test validation fails for oversized file."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        # 150 MB when limit is 100 MB
        result = service.validate_file("model.stl", 150 * 1024 * 1024)

        assert result['valid'] is False
        assert "size" in result['error'].lower()

    def test_validate_file_3mf(self):
        """Test validation for 3MF files."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = service.validate_file("model.3mf", 1024)

        assert result['valid'] is True
        assert result['file_type'] == '3mf'

    def test_validate_file_gcode(self):
        """Test validation for GCODE files."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = service.validate_file("model.gcode", 1024)

        assert result['valid'] is True
        assert result['file_type'] == 'gcode'

    def test_validate_file_uppercase_extension(self):
        """Test validation handles uppercase extensions."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = service.validate_file("MODEL.STL", 1024)

        assert result['valid'] is True


class TestDuplicateDetection:
    """Test duplicate file detection."""

    @pytest.mark.asyncio
    async def test_check_duplicate_not_found(self):
        """Test no duplicate found."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_db.get_connection.return_value = mock_conn
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = await service.check_duplicate("new_model.stl")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_duplicate_found(self):
        """Test duplicate is found."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        # Create an async context manager mock for the cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value={'id': 'existing_123'})

        # Create async context manager that returns the cursor
        @asynccontextmanager
        async def mock_execute(*args, **kwargs):
            yield mock_cursor

        mock_conn = MagicMock()
        mock_conn.execute = mock_execute
        mock_db.get_connection.return_value = mock_conn

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = await service.check_duplicate("existing_model.stl")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_duplicate_error_handling(self):
        """Test duplicate check handles errors gracefully."""
        mock_db = MagicMock()
        mock_db.get_connection.side_effect = Exception("Database error")
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        result = await service.check_duplicate("test.stl")

        assert result is False  # Returns False on error


class TestFileSaving:
    """Test file saving functionality."""

    @pytest.mark.asyncio
    async def test_save_uploaded_file_success(self):
        """Test successful file save."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            upload_file = MockUploadFile("test.stl", b"test content")

            result = await service.save_uploaded_file(upload_file, Path(tmpdir))

            assert result['success'] is True
            assert result['file_size'] == 12
            assert Path(result['file_path']).exists()

    @pytest.mark.asyncio
    async def test_save_uploaded_file_creates_directory(self):
        """Test file save creates destination directory."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_subdir"
            upload_file = MockUploadFile("test.stl", b"content")

            result = await service.save_uploaded_file(upload_file, new_dir)

            assert result['success'] is True
            assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_save_uploaded_file_error_handling(self):
        """Test file save handles errors."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        upload_file = MockUploadFile("test.stl", b"content")

        # Mock open to raise an error to test error handling
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch.object(Path, 'mkdir'):  # Mock mkdir to not actually create directories
                result = await service.save_uploaded_file(upload_file, Path("/nonexistent/readonly/path"))

        assert result['success'] is False
        assert result['error'] is not None


class TestHashCalculation:
    """Test file hash calculation."""

    @pytest.mark.asyncio
    async def test_calculate_file_hash(self):
        """Test SHA256 hash calculation."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content for hashing")
            f.flush()

            file_hash = await service.calculate_file_hash(Path(f.name))

            # Verify hash is 64 character hex string (SHA256)
            assert len(file_hash) == 64
            assert all(c in '0123456789abcdef' for c in file_hash)

    @pytest.mark.asyncio
    async def test_calculate_file_hash_consistent(self):
        """Test hash is consistent for same content."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event)

        content = b"identical content"

        with tempfile.NamedTemporaryFile(delete=False) as f1:
            f1.write(content)
            f1.flush()

            with tempfile.NamedTemporaryFile(delete=False) as f2:
                f2.write(content)
                f2.flush()

                hash1 = await service.calculate_file_hash(Path(f1.name))
                hash2 = await service.calculate_file_hash(Path(f2.name))

                assert hash1 == hash2


class TestFileRecordCreation:
    """Test database record creation."""

    @pytest.mark.asyncio
    async def test_create_file_record(self):
        """Test file record creation."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"content")
            f.flush()

            file_id = await service.create_file_record(
                filename="test.stl",
                file_path=f.name,
                file_size=7,
                file_type="stl",
                is_business=True,
                notes="Test notes"
            )

            assert file_id.startswith("upload_")
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_file_record_without_notes(self):
        """Test file record creation without notes."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"content")
            f.flush()

            file_id = await service.create_file_record(
                filename="test.stl",
                file_path=f.name,
                file_size=7,
                file_type="stl"
            )

            assert file_id.startswith("upload_")


class TestPostUploadProcessing:
    """Test post-upload processing."""

    @pytest.mark.asyncio
    async def test_process_file_with_library(self):
        """Test post-processing with library service."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_library = MagicMock()
        mock_library.add_file_from_upload = AsyncMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event, library_service=mock_library)

        await service.process_file_after_upload("file_123", "/path/to/file.stl")

        mock_library.add_file_from_upload.assert_called_once_with("file_123", "/path/to/file.stl")

    @pytest.mark.asyncio
    async def test_process_file_with_thumbnail(self):
        """Test post-processing with thumbnail service."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_thumbnail = MagicMock()
        mock_thumbnail.process_file_thumbnails = AsyncMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event, thumbnail_service=mock_thumbnail)

        await service.process_file_after_upload("file_123", "/path/to/file.stl")

        mock_thumbnail.process_file_thumbnails.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_file_with_metadata(self):
        """Test post-processing with metadata service."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.extract_enhanced_metadata = AsyncMock()

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event, metadata_service=mock_metadata)

        await service.process_file_after_upload("file_123", "/path/to/file.stl")

        mock_metadata.extract_enhanced_metadata.assert_called_once_with("file_123")

    @pytest.mark.asyncio
    async def test_process_file_service_error_handling(self):
        """Test post-processing handles service errors gracefully."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_library = MagicMock()
        mock_library.add_file_from_upload = AsyncMock(side_effect=Exception("Library error"))

        with patch('src.services.file_upload_service.get_settings', return_value=MockSettings()):
            with patch('src.services.file_upload_service.FileRepository'):
                service = FileUploadService(mock_db, mock_event, library_service=mock_library)

        # Should not raise
        await service.process_file_after_upload("file_123", "/path/to/file.stl")


class TestMultiFileUpload:
    """Test multiple file upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_files_success(self):
        """Test successful multiple file upload."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        settings = MockSettings()

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings.downloads_path = tmpdir

            files = [
                MockUploadFile("model1.stl", b"content 1"),
                MockUploadFile("model2.stl", b"content 2")
            ]

            # Mock duplicate check
            service.check_duplicate = AsyncMock(return_value=False)

            result = await service.upload_files(files)

            assert result['total_count'] == 2
            assert result['success_count'] == 2
            assert result['failure_count'] == 0
            assert len(result['uploaded_files']) == 2

    @pytest.mark.asyncio
    async def test_upload_files_partial_failure(self):
        """Test upload with some files failing validation."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        settings = MockSettings()

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings.downloads_path = tmpdir

            files = [
                MockUploadFile("model.stl", b"valid"),
                MockUploadFile("document.pdf", b"invalid"),  # Invalid extension
            ]

            service.check_duplicate = AsyncMock(return_value=False)

            result = await service.upload_files(files)

            assert result['total_count'] == 2
            assert result['success_count'] == 1
            assert result['failure_count'] == 1

    @pytest.mark.asyncio
    async def test_upload_files_duplicate_rejection(self):
        """Test duplicate files are rejected."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        settings = MockSettings()

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings.downloads_path = tmpdir

            files = [MockUploadFile("existing.stl", b"content")]

            service.check_duplicate = AsyncMock(return_value=True)

            result = await service.upload_files(files)

            assert result['success_count'] == 0
            assert result['failure_count'] == 1
            assert "already exists" in result['failed_files'][0]['error']

    @pytest.mark.asyncio
    async def test_upload_files_emits_events(self):
        """Test events are emitted during upload."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        settings = MockSettings()

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings.downloads_path = tmpdir

            files = [MockUploadFile("model.stl", b"content")]
            service.check_duplicate = AsyncMock(return_value=False)

            await service.upload_files(files)

            # Should emit started and complete events
            event_names = [call[0][0] for call in mock_event.emit_event.call_args_list]
            assert "file_upload_started" in event_names
            assert "file_upload_complete" in event_names

    @pytest.mark.asyncio
    async def test_upload_files_with_business_flag(self):
        """Test business flag is passed through."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)

        settings = MockSettings()

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings.downloads_path = tmpdir

            files = [MockUploadFile("model.stl", b"content")]
            service.check_duplicate = AsyncMock(return_value=False)

            await service.upload_files(files, is_business=True, notes="Customer order")

            # Verify create was called with business data
            create_call = mock_repo.create.call_args
            file_data = create_call[0][0]
            assert '"is_business": true' in file_data['metadata']

    @pytest.mark.asyncio
    async def test_upload_files_records_usage_stats(self):
        """Test usage statistics are recorded."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_event = MagicMock()
        mock_event.emit_event = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value=True)
        mock_usage = MagicMock()
        mock_usage.record_event = AsyncMock()

        settings = MockSettings()

        with patch('src.services.file_upload_service.get_settings', return_value=settings):
            with patch('src.services.file_upload_service.FileRepository', return_value=mock_repo):
                service = FileUploadService(mock_db, mock_event, usage_stats_service=mock_usage)

        with tempfile.TemporaryDirectory() as tmpdir:
            settings.downloads_path = tmpdir

            files = [MockUploadFile("model.stl", b"content")]
            service.check_duplicate = AsyncMock(return_value=False)

            await service.upload_files(files)

            mock_usage.record_event.assert_called_once()
            call_args = mock_usage.record_event.call_args
            assert call_args[0][0] == "file_uploaded"
