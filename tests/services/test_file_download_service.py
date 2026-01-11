"""
Unit tests for FileDownloadService.

Tests the file download functionality including:
- Successful downloads
- Failed downloads
- Progress tracking
- Event emissions
- Database updates
- Library integration
- Path validation and security
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path
import tempfile
import os


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_success(file_download_service, event_service, async_database):
    """Test successful file download."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"
    file_id = f"{printer_id}_{filename}"

    # Mock printer service
    mock_printer_service = AsyncMock()
    mock_printer_service.download_printer_file = AsyncMock(return_value=True)
    mock_printer_service.get_printer = AsyncMock(return_value={
        'id': printer_id,
        'name': 'Bambu A1',
        'type': 'bambu_lab'
    })
    file_download_service.set_printer_service(mock_printer_service)

    # Create temporary download directory
    with tempfile.TemporaryDirectory() as temp_dir:
        destination = os.path.join(temp_dir, filename)

        # Create mock file to simulate successful download
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wb') as f:
            f.write(b"mock 3mf file content")

        # Mock database methods
        file_download_service.database.update_file = AsyncMock()

        # Mock destination path creation to use our temp directory
        async def mock_create_path(pid, fname):
            return destination
        file_download_service._create_destination_path = mock_create_path

        # Track emitted events
        events_emitted = []
        async def capture_event(event_type, data):
            events_emitted.append({"type": event_type, "data": data})

        file_download_service.event_service.emit_event = capture_event

        # Act
        result = await file_download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "success"
        assert result["message"] == "File downloaded successfully"
        assert result["local_path"] == destination
        assert result["file_id"] == file_id
        assert result["file_size"] > 0

        # Verify events emitted
        event_types = [e["type"] for e in events_emitted]
        assert "file_download_started" in event_types
        assert "file_needs_thumbnail_processing" in event_types
        assert "file_download_complete" in event_types

        # Verify download progress tracking
        assert file_download_service.download_progress[file_id] == 100
        assert file_download_service.download_status[file_id] == "completed"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_no_printer_service(file_download_service):
    """Test download fails when printer service not available."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"

    # Ensure printer service is None
    file_download_service.printer_service = None

    # Act
    result = await file_download_service.download_file(printer_id, filename)

    # Assert
    assert result["status"] == "error"
    assert "Printer service not available" in result["message"]
    assert result["local_path"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_printer_failure(file_download_service):
    """Test download when printer service returns failure."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"
    file_id = f"{printer_id}_{filename}"

    # Mock printer service that fails download
    mock_printer_service = AsyncMock()
    mock_printer_service.download_printer_file = AsyncMock(return_value=False)
    file_download_service.set_printer_service(mock_printer_service)

    # Mock destination path
    with tempfile.TemporaryDirectory() as temp_dir:
        destination = os.path.join(temp_dir, filename)
        async def mock_create_path(pid, fname):
            return destination
        file_download_service._create_destination_path = mock_create_path

        # Track emitted events
        events_emitted = []
        async def capture_event(event_type, data):
            events_emitted.append({"type": event_type, "data": data})
        file_download_service.event_service.emit_event = capture_event

        # Act
        result = await file_download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "error"
        assert "Download failed" in result["message"]
        assert result["local_path"] is None
        assert file_download_service.download_status[file_id] == "failed"

        # Verify failure event emitted
        event_types = [e["type"] for e in events_emitted]
        assert "file_download_failed" in event_types


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_with_custom_destination(file_download_service):
    """Test download with custom destination path."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"

    # Mock printer service
    mock_printer_service = AsyncMock()
    mock_printer_service.download_printer_file = AsyncMock(return_value=True)
    file_download_service.set_printer_service(mock_printer_service)
    file_download_service.database.update_file = AsyncMock()

    # Create custom destination
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_dest = os.path.join(temp_dir, "custom", filename)
        Path(custom_dest).parent.mkdir(parents=True, exist_ok=True)

        # Create mock file
        with open(custom_dest, 'wb') as f:
            f.write(b"mock file")

        # Mock event emission
        file_download_service.event_service.emit_event = AsyncMock()

        # Act
        result = await file_download_service.download_file(
            printer_id,
            filename,
            destination_path=custom_dest
        )

        # Assert
        assert result["status"] == "success"
        assert result["local_path"] == custom_dest


@pytest.mark.unit
def test_validate_safe_path_valid(file_download_service):
    """Test path validation with valid path."""
    # Arrange
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        filename = "model.3mf"

        # Act
        result = file_download_service._validate_safe_path(base_dir, filename)

        # Assert
        assert str(result).startswith(str(base_dir))
        assert filename in str(result)


@pytest.mark.unit
def test_validate_safe_path_traversal_attempt(file_download_service):
    """Test path validation blocks path traversal attempts."""
    # Arrange
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        malicious_filename = "../../../etc/passwd"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            file_download_service._validate_safe_path(base_dir, malicious_filename)

        assert "Path traversal detected" in str(exc_info.value)


@pytest.mark.unit
def test_validate_safe_path_absolute_attempt(file_download_service):
    """Test path validation blocks absolute path attempts."""
    # Arrange
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        malicious_filename = "/etc/shadow"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            file_download_service._validate_safe_path(base_dir, malicious_filename)

        assert "Path traversal detected" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_download_status_active(file_download_service):
    """Test getting status for active download."""
    # Arrange
    file_id = "bambu_001_model.3mf"
    file_download_service.download_status[file_id] = "downloading"
    file_download_service.download_progress[file_id] = 45

    # Act
    status = await file_download_service.get_download_status(file_id)

    # Assert
    assert status["file_id"] == file_id
    assert status["status"] == "downloading"
    assert status["progress"] == 45


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_download_status_not_found(file_download_service):
    """Test getting status for non-existent file."""
    # Arrange
    file_id = "nonexistent_file"
    file_download_service.database.list_files = AsyncMock(return_value=[])

    # Act
    status = await file_download_service.get_download_status(file_id)

    # Assert
    assert status["file_id"] == file_id
    assert status["status"] == "not_found"
    assert status["progress"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_download_status(file_download_service):
    """Test cleanup of old download status entries."""
    # Arrange
    file_download_service.download_status = {
        "file1": "completed",
        "file2": "failed",
        "file3": "downloading",
        "file4": "completed"
    }
    file_download_service.download_progress = {
        "file1": 100,
        "file2": 50,
        "file3": 30,
        "file4": 100
    }

    # Act
    await file_download_service.cleanup_download_status()

    # Assert
    # Completed and failed should be removed
    assert "file1" not in file_download_service.download_status
    assert "file2" not in file_download_service.download_status
    assert "file4" not in file_download_service.download_status

    # In-progress should remain
    assert "file3" in file_download_service.download_status
    assert file_download_service.download_status["file3"] == "downloading"


@pytest.mark.unit
def test_extract_printer_info_bambu_lab(file_download_service):
    """Test extracting printer info for Bambu Lab printer."""
    # Arrange
    printer = {
        'type': 'bambu_lab',
        'name': 'My Bambu A1 Printer'
    }

    # Act
    info = file_download_service._extract_printer_info(printer)

    # Assert
    assert info['manufacturer'] == 'bambu_lab'
    assert info['printer_model'] == 'A1'


@pytest.mark.unit
def test_extract_printer_info_prusa(file_download_service):
    """Test extracting printer info for Prusa printer."""
    # Arrange
    printer = {
        'type': 'prusa_core',
        'name': 'Prusa Core One'
    }

    # Act
    info = file_download_service._extract_printer_info(printer)

    # Assert
    assert info['manufacturer'] == 'prusa_research'
    assert info['printer_model'] == 'Core One'


@pytest.mark.unit
def test_extract_printer_info_unknown(file_download_service):
    """Test extracting printer info for unknown printer."""
    # Arrange
    printer = {
        'type': 'unknown_type',
        'name': 'Some Printer'
    }

    # Act
    info = file_download_service._extract_printer_info(printer)

    # Assert
    assert info['manufacturer'] == 'unknown'
    # Should use printer name as fallback
    assert info['printer_model'] == 'Some Printer'


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_library_integration(file_download_service):
    """Test download with library integration enabled."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"

    # Mock printer service
    mock_printer_service = AsyncMock()
    mock_printer_service.download_printer_file = AsyncMock(return_value=True)
    # Return a mock Printer object with proper attributes (not a dict)
    mock_printer = MagicMock()
    mock_printer.id = printer_id
    mock_printer.name = 'Bambu A1'
    mock_printer.type = 'bambu_lab'
    mock_printer.dict = MagicMock(return_value={
        'id': printer_id,
        'name': 'Bambu A1',
        'type': 'bambu_lab',
        'manufacturer': 'Bambu Lab',
        'model': 'A1'
    })
    mock_printer_service.get_printer = AsyncMock(return_value=mock_printer)
    file_download_service.set_printer_service(mock_printer_service)

    # Mock library service
    mock_library_service = AsyncMock()
    mock_library_service.enabled = True
    mock_library_service.add_file_to_library = AsyncMock()
    file_download_service.set_library_service(mock_library_service)

    # Mock database and event service
    file_download_service.database.update_file = AsyncMock()
    file_download_service.event_service.emit_event = AsyncMock()

    # Create temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        destination = os.path.join(temp_dir, filename)
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wb') as f:
            f.write(b"mock content")

        # Mock destination path creation
        async def mock_create_path(pid, fname):
            return destination
        file_download_service._create_destination_path = mock_create_path

        # Act
        result = await file_download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "success"

        # Verify library service was called
        mock_library_service.add_file_to_library.assert_called_once()
        call_args = mock_library_service.add_file_to_library.call_args
        assert call_args[1]['copy_file'] is True
        assert 'source_info' in call_args[1]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_verifies_file_exists(file_download_service):
    """Test that download verifies file actually exists after download."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"

    # Mock printer service that reports success
    mock_printer_service = AsyncMock()
    mock_printer_service.download_printer_file = AsyncMock(return_value=True)
    file_download_service.set_printer_service(mock_printer_service)
    file_download_service.database.update_file = AsyncMock()

    # Mock destination path that doesn't actually create a file
    with tempfile.TemporaryDirectory() as temp_dir:
        destination = os.path.join(temp_dir, "nonexistent.3mf")

        async def mock_create_path(pid, fname):
            return destination
        file_download_service._create_destination_path = mock_create_path

        file_download_service.event_service.emit_event = AsyncMock()

        # Act
        result = await file_download_service.download_file(printer_id, filename)

        # Assert - should detect file doesn't exist
        assert result["status"] == "error"
        assert "file not found" in result["message"].lower()


@pytest.mark.unit
def test_set_services(file_download_service):
    """Test setting service dependencies."""
    # Arrange
    mock_printer = MagicMock()
    mock_config = MagicMock()
    mock_library = MagicMock()

    # Act
    file_download_service.set_printer_service(mock_printer)
    file_download_service.set_config_service(mock_config)
    file_download_service.set_library_service(mock_library)

    # Assert
    assert file_download_service.printer_service == mock_printer
    assert file_download_service.config_service == mock_config
    assert file_download_service.library_service == mock_library


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_exception_handling(file_download_service):
    """Test download handles exceptions gracefully."""
    # Arrange
    printer_id = "bambu_001"
    filename = "model.3mf"

    # Mock printer service that raises exception
    mock_printer_service = AsyncMock()
    mock_printer_service.download_printer_file = AsyncMock(
        side_effect=Exception("Network error")
    )
    file_download_service.set_printer_service(mock_printer_service)

    with tempfile.TemporaryDirectory() as temp_dir:
        destination = os.path.join(temp_dir, filename)
        async def mock_create_path(pid, fname):
            return destination
        file_download_service._create_destination_path = mock_create_path

        file_download_service.event_service.emit_event = AsyncMock()

        # Act
        result = await file_download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "error"
        assert "Network error" in result["message"]
        assert result["local_path"] is None
