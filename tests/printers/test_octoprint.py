"""
Unit tests for OctoPrintPrinter.

Tests the OctoPrint printer integration including:
- Initialization with HTTP API and SockJS
- Connection management (connect/disconnect)
- Status retrieval via REST API and WebSocket
- Job information retrieval
- File listing and downloads
- Print control operations (pause/resume/stop)
- Camera functionality
- Status mapping
- Error handling and retries
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import aiohttp

from src.models.printer import PrinterStatus


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession."""
    session = MagicMock()
    session.get = MagicMock()
    session.post = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_octoprint_version_response():
    """Create mock OctoPrint version response."""
    return {
        'server': '1.9.3',
        'api': '0.1',
        'text': 'OctoPrint 1.9.3'
    }


@pytest.fixture
def mock_octoprint_printer_response():
    """Create mock OctoPrint printer status response."""
    return {
        'state': {
            'text': 'Operational',
            'flags': {
                'operational': True,
                'paused': False,
                'printing': False,
                'cancelling': False,
                'sdReady': True,
                'error': False,
                'ready': True,
                'closedOrError': False
            }
        },
        'temperature': {
            'bed': {'actual': 60.0, 'target': 60.0, 'offset': 0},
            'tool0': {'actual': 220.0, 'target': 220.0, 'offset': 0}
        }
    }


@pytest.fixture
def mock_octoprint_job_response():
    """Create mock OctoPrint job response."""
    return {
        'job': {
            'file': {
                'name': 'test_model.gcode',
                'display': 'Test Model',
                'origin': 'local',
                'size': 1234567,
                'date': 1704067200
            },
            'estimatedPrintTime': 7200,
            'filament': {
                'tool0': {'length': 5000, 'volume': 12.5}
            }
        },
        'progress': {
            'completion': 45.0,
            'printTime': 3600,
            'printTimeLeft': 3600,
            'filepos': 500000
        },
        'state': 'Printing'
    }


@pytest.fixture
def mock_octoprint_files_response():
    """Create mock OctoPrint files response."""
    return {
        'files': [
            {
                'name': 'model1.gcode',
                'path': 'model1.gcode',
                'type': 'machinecode',
                'origin': 'local',
                'size': 1000000,
                'date': 1704067200
            },
            {
                'name': 'folder1',
                'path': 'folder1',
                'type': 'folder',
                'children': [
                    {
                        'name': 'model2.gcode',
                        'path': 'folder1/model2.gcode',
                        'type': 'machinecode',
                        'origin': 'local',
                        'size': 2000000,
                        'date': 1704153600
                    }
                ]
            }
        ],
        'free': 10000000000,
        'total': 20000000000
    }


@pytest.mark.unit
class TestOctoPrintPrinterInitialization:
    """Test OctoPrintPrinter initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Workshop OctoPrint',
            ip_address='192.168.1.100',
            api_key='test-api-key-12345'
        )

        assert printer.printer_id == 'octoprint_001'
        assert printer.name == 'Workshop OctoPrint'
        assert printer.ip_address == '192.168.1.100'
        assert printer.api_key == 'test-api-key-12345'
        assert printer.port == 80
        assert printer.use_https is False
        assert printer.base_url == 'http://192.168.1.100'
        assert printer.api_url == 'http://192.168.1.100/api'
        assert printer.session is None
        assert printer.is_connected is False

    def test_init_with_custom_port(self):
        """Test initialization with custom port."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_002',
            name='OctoPrint Custom Port',
            ip_address='192.168.1.101',
            api_key='test-key',
            port=5000
        )

        assert printer.port == 5000
        assert printer.base_url == 'http://192.168.1.101:5000'
        assert printer.api_url == 'http://192.168.1.101:5000/api'

    def test_init_with_https(self):
        """Test initialization with HTTPS."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_003',
            name='OctoPrint HTTPS',
            ip_address='192.168.1.102',
            api_key='test-key',
            use_https=True
        )

        assert printer.use_https is True
        assert printer.base_url == 'https://192.168.1.102'

    def test_init_with_https_and_custom_port(self):
        """Test initialization with HTTPS and custom port."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_004',
            name='OctoPrint HTTPS Custom',
            ip_address='192.168.1.103',
            api_key='test-key',
            port=8443,
            use_https=True
        )

        assert printer.base_url == 'https://192.168.1.103:8443'

    def test_init_with_file_service(self):
        """Test initialization with optional file service."""
        from src.printers.octoprint import OctoPrintPrinter

        mock_file_service = MagicMock()
        printer = OctoPrintPrinter(
            printer_id='octoprint_005',
            name='OctoPrint with FileService',
            ip_address='192.168.1.104',
            api_key='test-key',
            file_service=mock_file_service
        )

        assert printer.file_service == mock_file_service


@pytest.mark.unit
class TestOctoPrintStatusMapping:
    """Test OctoPrint status mapping."""

    def test_map_operational_status(self):
        """Test mapping operational state to ONLINE."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        state = {
            'flags': {'operational': True, 'ready': True},
            'text': 'Operational'
        }

        result = printer._map_octoprint_status(state)
        assert result == PrinterStatus.ONLINE

    def test_map_printing_status(self):
        """Test mapping printing state."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        state = {
            'flags': {'printing': True, 'operational': True},
            'text': 'Printing'
        }

        result = printer._map_octoprint_status(state)
        assert result == PrinterStatus.PRINTING

    def test_map_paused_status(self):
        """Test mapping paused state."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        state = {
            'flags': {'paused': True, 'operational': True},
            'text': 'Paused'
        }

        result = printer._map_octoprint_status(state)
        assert result == PrinterStatus.PAUSED

    def test_map_error_status(self):
        """Test mapping error state."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        state = {
            'flags': {'error': True},
            'text': 'Error'
        }

        result = printer._map_octoprint_status(state)
        assert result == PrinterStatus.ERROR

    def test_map_offline_status(self):
        """Test mapping offline/closed state."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        state = {
            'flags': {'closedOrError': True, 'closed': True},
            'text': 'Offline'
        }

        result = printer._map_octoprint_status(state)
        assert result == PrinterStatus.OFFLINE

    def test_map_none_status(self):
        """Test mapping None state returns UNKNOWN."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        result = printer._map_octoprint_status(None)
        assert result == PrinterStatus.UNKNOWN

    def test_map_status_text_fallback(self):
        """Test status mapping falls back to text parsing."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='test',
            name='Test',
            ip_address='127.0.0.1',
            api_key='key'
        )

        # No flags, but text indicates printing
        state = {
            'flags': {},
            'text': 'Printing from SD'
        }

        result = printer._map_octoprint_status(state)
        assert result == PrinterStatus.PRINTING


@pytest.mark.unit
@pytest.mark.asyncio
class TestOctoPrintPrinterConnection:
    """Test OctoPrintPrinter connection management."""

    @patch('aiohttp.ClientSession')
    async def test_connect_success(self, mock_session_class, mock_octoprint_version_response):
        """Test successful connection."""
        from src.printers.octoprint import OctoPrintPrinter

        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_octoprint_version_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test OctoPrint',
            ip_address='192.168.1.100',
            api_key='test-api-key'
        )

        # Mock SockJS client
        with patch.object(printer, '_connect_sockjs', new_callable=AsyncMock):
            result = await printer.connect()

        assert result is True
        assert printer.is_connected is True
        assert printer.session is not None
        mock_session.get.assert_called()

    @patch('aiohttp.ClientSession')
    async def test_connect_auth_failure(self, mock_session_class):
        """Test connection failure with authentication error."""
        from src.printers.octoprint import OctoPrintPrinter
        from src.utils.errors import PrinterConnectionError

        # Setup mock 401 response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        mock_session_class.return_value = mock_session

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test OctoPrint',
            ip_address='192.168.1.100',
            api_key='invalid-key'
        )

        with pytest.raises(PrinterConnectionError):
            await printer.connect()

        assert printer.is_connected is False

    async def test_disconnect(self):
        """Test disconnection."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test OctoPrint',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        # Setup mock session
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        printer.session = mock_session
        printer.is_connected = True

        # Setup mock SockJS client
        mock_sockjs = MagicMock()
        mock_sockjs.disconnect = AsyncMock()
        printer.sockjs_client = mock_sockjs

        await printer.disconnect()

        assert printer.is_connected is False
        assert printer.session is None
        mock_session.close.assert_called_once()
        mock_sockjs.disconnect.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestOctoPrintJobControl:
    """Test OctoPrintPrinter job control operations."""

    async def test_pause_print(self):
        """Test pause print operation."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        # Setup mock session
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.pause_print()

        assert result is True
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert 'json' in call_args.kwargs
        assert call_args.kwargs['json']['command'] == 'pause'
        assert call_args.kwargs['json']['action'] == 'pause'

    async def test_resume_print(self):
        """Test resume print operation."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.resume_print()

        assert result is True
        call_args = mock_session.post.call_args
        assert call_args.kwargs['json']['command'] == 'pause'
        assert call_args.kwargs['json']['action'] == 'resume'

    async def test_stop_print(self):
        """Test stop/cancel print operation."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.stop_print()

        assert result is True
        call_args = mock_session.post.call_args
        assert call_args.kwargs['json']['command'] == 'cancel'

    async def test_job_command_conflict(self):
        """Test job command with 409 conflict response."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 409  # Conflict - invalid state
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.pause_print()

        assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestOctoPrintFileOperations:
    """Test OctoPrintPrinter file operations."""

    async def test_list_files(self, mock_octoprint_files_response):
        """Test file listing."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_octoprint_files_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        printer.session = mock_session

        files = await printer.list_files()

        assert len(files) == 2
        assert files[0].filename == 'model1.gcode'
        assert files[1].filename == 'model2.gcode'
        assert files[1].path == 'local/folder1/model2.gcode'


@pytest.mark.unit
@pytest.mark.asyncio
class TestOctoPrintCameraOperations:
    """Test OctoPrintPrinter camera operations."""

    async def test_has_camera_enabled(self):
        """Test camera detection when enabled."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'webcam': {
                'webcamEnabled': True,
                'streamUrl': '/webcam/?action=stream',
                'snapshotUrl': '/webcam/?action=snapshot'
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.has_camera()
        assert result is True

    async def test_has_camera_disabled(self):
        """Test camera detection when disabled."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'webcam': {
                'webcamEnabled': False
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.has_camera()
        assert result is False

    async def test_get_camera_stream_url(self):
        """Test getting camera stream URL."""
        from src.printers.octoprint import OctoPrintPrinter

        printer = OctoPrintPrinter(
            printer_id='octoprint_001',
            name='Test',
            ip_address='192.168.1.100',
            api_key='test-key'
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'webcam': {
                'webcamEnabled': True,
                'streamUrl': '/webcam/?action=stream'
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        printer.session = mock_session

        result = await printer.get_camera_stream_url()
        assert result == 'http://192.168.1.100/webcam/?action=stream'


@pytest.mark.unit
class TestOctoPrintPrinterType:
    """Test OctoPrint printer type enum."""

    def test_octoprint_enum_exists(self):
        """Test OCTOPRINT enum value exists."""
        from src.models.printer import PrinterType

        assert hasattr(PrinterType, 'OCTOPRINT')
        assert PrinterType.OCTOPRINT.value == 'octoprint'


@pytest.mark.unit
class TestOctoPrintConfig:
    """Test OctoPrint configuration validation."""

    def test_valid_octoprint_config(self):
        """Test valid OctoPrint configuration."""
        from src.services.config_service import PrinterConfig

        config = PrinterConfig(
            printer_id='octoprint_001',
            name='Test OctoPrint',
            type='octoprint',
            ip_address='192.168.1.100',
            api_key='test-api-key'
        )

        assert config.type == 'octoprint'
        assert config.ip_address == '192.168.1.100'
        assert config.api_key == 'test-api-key'

    def test_invalid_octoprint_config_missing_ip(self):
        """Test invalid OctoPrint config without IP address."""
        from src.services.config_service import PrinterConfig

        with pytest.raises(ValueError, match="requires ip_address and api_key"):
            PrinterConfig(
                printer_id='octoprint_001',
                name='Test OctoPrint',
                type='octoprint',
                api_key='test-api-key'
            )

    def test_invalid_octoprint_config_missing_api_key(self):
        """Test invalid OctoPrint config without API key."""
        from src.services.config_service import PrinterConfig

        with pytest.raises(ValueError, match="requires ip_address and api_key"):
            PrinterConfig(
                printer_id='octoprint_001',
                name='Test OctoPrint',
                type='octoprint',
                ip_address='192.168.1.100'
            )

    def test_octoprint_config_with_port(self):
        """Test OctoPrint config with custom port."""
        from src.services.config_service import PrinterConfig

        config = PrinterConfig(
            printer_id='octoprint_001',
            name='Test OctoPrint',
            type='octoprint',
            ip_address='192.168.1.100',
            api_key='test-api-key',
            port=5000
        )

        assert config.port == 5000

    def test_octoprint_config_with_https(self):
        """Test OctoPrint config with HTTPS."""
        from src.services.config_service import PrinterConfig

        config = PrinterConfig(
            printer_id='octoprint_001',
            name='Test OctoPrint',
            type='octoprint',
            ip_address='192.168.1.100',
            api_key='test-api-key',
            use_https=True
        )

        assert config.use_https is True
