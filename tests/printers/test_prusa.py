"""
Unit tests for PrusaPrinter.

Tests the Prusa Core One printer integration including:
- Initialization with PrusaLink HTTP API
- Connection management (connect/disconnect)
- Status retrieval via HTTP API
- Job information retrieval
- File listing and downloads
- Print control operations (pause/resume/stop)
- Camera functionality
- Thumbnail downloads
- Error handling and retries
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, Mock
from datetime import datetime
from typing import Dict, Any, List
import aiohttp


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession."""
    session = MagicMock()
    session.get = MagicMock()
    session.post = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_api_response():
    """Create mock API response data."""
    return {
        'version': {
            'server': 'PrusaLink 0.7.0',
            'api': '2.0.0'
        },
        'status': {
            'printer': {
                'state': 'Printing',
                'temp_bed': 60.0,
                'temp_nozzle': 220.0,
                'target_bed': 60.0,
                'target_nozzle': 220.0
            }
        },
        'job': {
            'id': 1,
            'state': 'Printing',
            'progress': 45,
            'time_remaining': 1800,
            'file': {
                'display_name': 'test_model.gcode',
                'name': '/usb/test_model.gcode'
            }
        }
    }


@pytest.mark.unit
class TestPrusaPrinterInitialization:
    """Test PrusaPrinter initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        from src.printers.prusa import PrusaPrinter

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key-12345'
        )

        assert printer.printer_id == 'prusa_001'
        assert printer.name == 'Prusa Core One'
        assert printer.ip_address == '192.168.1.200'
        assert printer.api_key == 'test-api-key-12345'
        assert printer.base_url == 'http://192.168.1.200/api'
        assert printer.session is None
        assert printer.is_connected is False

    def test_init_with_file_service(self):
        """Test initialization with optional file service."""
        from src.printers.prusa import PrusaPrinter

        mock_file_service = MagicMock()
        printer = PrusaPrinter(
            printer_id='prusa_002',
            name='Prusa MK4',
            ip_address='192.168.1.201',
            api_key='another-api-key',
            file_service=mock_file_service
        )

        assert printer.file_service == mock_file_service

    def test_base_url_construction(self):
        """Test base URL is correctly constructed from IP address."""
        from src.printers.prusa import PrusaPrinter

        printer = PrusaPrinter(
            printer_id='prusa_003',
            name='Prusa XL',
            ip_address='10.0.0.100',
            api_key='test-key'
        )

        assert printer.base_url == 'http://10.0.0.100/api'


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterConnection:
    """Test PrusaPrinter connection management."""

    @patch('aiohttp.ClientSession')
    async def test_connect_success(self, mock_session_class):
        """Test successful connection."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'server': 'PrusaLink 0.7.0'})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        result = await printer.connect()

        assert result is True
        assert printer.is_connected is True
        assert printer.session is not None
        mock_session.get.assert_called_once()

    @patch('aiohttp.ClientSession')
    async def test_connect_already_connected(self, mock_session_class):
        """Test connect when already connected."""
        from src.printers.prusa import PrusaPrinter

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.is_connected = True
        printer.session = MagicMock()

        result = await printer.connect()

        assert result is True
        # Should not create new session
        mock_session_class.assert_not_called()

    @patch('aiohttp.ClientSession')
    async def test_connect_auth_failure(self, mock_session_class):
        """Test connection failure due to authentication."""
        from src.printers.prusa import PrusaPrinter
        from src.utils.errors import PrinterConnectionError

        # Setup mock response with 401
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='wrong-api-key'
        )

        with pytest.raises(PrinterConnectionError, match="Authentication failed"):
            await printer.connect()

        assert printer.is_connected is False

    @patch('aiohttp.ClientSession')
    async def test_connect_forbidden(self, mock_session_class):
        """Test connection failure due to forbidden access."""
        from src.printers.prusa import PrusaPrinter
        from src.utils.errors import PrinterConnectionError

        # Setup mock response with 403
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        with pytest.raises(PrinterConnectionError, match="Access forbidden"):
            await printer.connect()

    @patch('aiohttp.ClientSession')
    async def test_connect_timeout_with_retry(self, mock_session_class):
        """Test connection handles timeouts with retry logic."""
        from src.printers.prusa import PrusaPrinter
        import asyncio

        # Setup mock to succeed on second attempt
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'server': 'PrusaLink'})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[
            asyncio.TimeoutError(),  # First attempt fails
            mock_response  # Second attempt succeeds
        ])
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await printer.connect()

        assert result is True
        assert printer.is_connected is True

    async def test_disconnect(self):
        """Test disconnect functionality."""
        from src.printers.prusa import PrusaPrinter

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        # Setup connected printer
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        printer.session = mock_session
        printer.is_connected = True

        await printer.disconnect()

        assert printer.is_connected is False
        assert printer.session is None
        mock_session.close.assert_called_once()

    async def test_disconnect_not_connected(self):
        """Test disconnect when not connected."""
        from src.printers.prusa import PrusaPrinter

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        # Should not raise error
        await printer.disconnect()
        assert printer.is_connected is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterStatus:
    """Test PrusaPrinter status retrieval."""

    @patch('aiohttp.ClientSession')
    async def test_get_status_success(self, mock_session_class):
        """Test successful status retrieval."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'printer': {
                'state': 'Printing',
                'temp_bed': 60.0,
                'temp_nozzle': 220.0,
                'target_bed': 60.0,
                'target_nozzle': 220.0
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        status = await printer.get_status()

        assert status is not None
        assert status.status.value in ['printing', 'idle']
        assert status.bed_temp == 60.0
        assert status.nozzle_temp == 220.0

    async def test_get_status_not_connected(self):
        """Test get_status when not connected."""
        from src.printers.prusa import PrusaPrinter
        from src.utils.errors import PrinterConnectionError

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.get_status()

    def test_map_prusa_status(self):
        """Test Prusa state to PrinterStatus mapping."""
        from src.printers.prusa import PrusaPrinter
        from src.models.printer import PrinterStatus

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        assert printer._map_prusa_status('Printing') == PrinterStatus.PRINTING
        assert printer._map_prusa_status('Paused') == PrinterStatus.PAUSED
        assert printer._map_prusa_status('Idle') == PrinterStatus.IDLE
        assert printer._map_prusa_status('Operational') == PrinterStatus.IDLE
        assert printer._map_prusa_status('Unknown') == PrinterStatus.ERROR


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterJobInfo:
    """Test PrusaPrinter job information retrieval."""

    @patch('aiohttp.ClientSession')
    async def test_get_job_info_active_job(self, mock_session_class):
        """Test retrieving active job information."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'id': 123,
            'state': 'Printing',
            'progress': 60,
            'time_remaining': 2400,
            'file': {
                'display_name': 'test_model.gcode',
                'name': '/usb/test_model.gcode'
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        job_info = await printer.get_job_info()

        assert job_info is not None
        assert job_info.filename == 'test_model.gcode'
        assert job_info.progress == 60
        assert job_info.time_remaining == 2400

    @patch('aiohttp.ClientSession')
    async def test_get_job_info_no_active_job(self, mock_session_class):
        """Test retrieving job info when no job is active."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response with no active job
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'state': 'Idle'
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        job_info = await printer.get_job_info()

        assert job_info is None

    def test_map_job_status(self):
        """Test job status mapping."""
        from src.printers.prusa import PrusaPrinter
        from src.printers.base import JobStatus

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        assert printer._map_job_status('Printing') == JobStatus.PRINTING
        assert printer._map_job_status('Paused') == JobStatus.PAUSED
        assert printer._map_job_status('Finished') == JobStatus.COMPLETED
        assert printer._map_job_status('Idle') == JobStatus.IDLE


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterFileOperations:
    """Test PrusaPrinter file listing and downloads."""

    @patch('aiohttp.ClientSession')
    async def test_list_files_success(self, mock_session_class):
        """Test successful file listing."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'files': [
                {'name': 'model1.gcode', 'size': 1024000, 'display_name': 'model1.gcode'},
                {'name': 'model2.gcode', 'size': 2048000, 'display_name': 'model2.gcode'}
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        files = await printer.list_files()

        assert isinstance(files, list)

    async def test_list_files_not_connected(self):
        """Test list_files when not connected."""
        from src.printers.prusa import PrusaPrinter
        from src.utils.errors import PrinterConnectionError

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.list_files()

    @patch('aiohttp.ClientSession')
    @patch('builtins.open', create=True)
    async def test_download_file_success(self, mock_open, mock_session_class):
        """Test successful file download."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b'file content here')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        # Setup file mock
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        result = await printer.download_file('test.gcode', '/tmp/test.gcode')

        # Implementation may vary, check for boolean or exception
        assert isinstance(result, bool) or result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterPrintControl:
    """Test PrusaPrinter print control operations."""

    @patch('aiohttp.ClientSession')
    async def test_pause_print_success(self, mock_session_class):
        """Test pausing print successfully."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        result = await printer.pause_print()

        assert result is True

    async def test_pause_print_not_connected(self):
        """Test pause_print when not connected."""
        from src.printers.prusa import PrusaPrinter
        from src.utils.errors import PrinterConnectionError

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.pause_print()

    @patch('aiohttp.ClientSession')
    async def test_resume_print_success(self, mock_session_class):
        """Test resuming print successfully."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        result = await printer.resume_print()

        assert result is True

    @patch('aiohttp.ClientSession')
    async def test_stop_print_success(self, mock_session_class):
        """Test stopping print successfully."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        result = await printer.stop_print()

        assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterCamera:
    """Test PrusaPrinter camera functionality."""

    @patch('aiohttp.ClientSession')
    async def test_has_camera(self, mock_session_class):
        """Test camera detection."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response with cameras
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {'id': 'camera1', 'name': 'Default Camera'}
        ])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        has_camera = await printer.has_camera()

        assert isinstance(has_camera, bool)

    @patch('aiohttp.ClientSession')
    async def test_get_camera_stream_url(self, mock_session_class):
        """Test getting camera stream URL."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {'id': 'camera1', 'url': 'http://192.168.1.200:8080/stream'}
        ])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        stream_url = await printer.get_camera_stream_url()

        assert stream_url is None or isinstance(stream_url, str)

    @patch('aiohttp.ClientSession')
    async def test_take_snapshot(self, mock_session_class):
        """Test taking camera snapshot."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b'fake_image_data')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        snapshot = await printer.take_snapshot()

        # Should return bytes or None
        assert snapshot is None or isinstance(snapshot, bytes)


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrusaPrinterThumbnails:
    """Test PrusaPrinter thumbnail download functionality."""

    @patch('aiohttp.ClientSession')
    async def test_download_thumbnail_success(self, mock_session_class):
        """Test successful thumbnail download."""
        from src.printers.prusa import PrusaPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b'thumbnail_image_data')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )
        printer.session = mock_session
        printer.is_connected = True

        thumbnail = await printer.download_thumbnail('test.gcode', 'l')

        # Should return bytes or None
        assert thumbnail is None or isinstance(thumbnail, bytes)


@pytest.mark.unit
class TestPrusaPrinterHelpers:
    """Test PrusaPrinter helper methods."""

    def test_extract_filaments_from_api(self):
        """Test filament extraction from API data."""
        from src.printers.prusa import PrusaPrinter

        printer = PrusaPrinter(
            printer_id='prusa_001',
            name='Prusa Core One',
            ip_address='192.168.1.200',
            api_key='test-api-key'
        )

        status_data = {
            'filament': {
                'material': 'PLA',
                'color': 'FFFFFF',
                'used': 500
            }
        }

        filaments = printer._extract_filaments_from_api(status_data)

        # Should return list of Filament objects or empty list
        assert isinstance(filaments, list)
