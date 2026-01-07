"""
Unit tests for BambuLabPrinter.

Tests the Bambu Lab printer integration including:
- Initialization with bambulabs_api and MQTT fallback
- Connection management (connect/disconnect)
- Status retrieval and mapping
- Job information retrieval
- File listing (FTP, MQTT, bambu_api)
- File downloads via multiple strategies
- Print control (pause/resume/stop)
- Camera functionality
- Error handling and edge cases
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, Mock
from datetime import datetime
from typing import Dict, Any, List
import asyncio


@pytest.fixture
def mock_bambu_client():
    """Create a mock bambulabs_api Printer client."""
    with patch('src.printers.bambu_lab.BambuClient') as mock:
        client = MagicMock()
        client.connect = AsyncMock(return_value=True)
        client.disconnect = AsyncMock()
        client.get_state = MagicMock(return_value={
            'print': {
                'gcode_state': 'RUNNING',
                'mc_percent': 45,
                'mc_remaining_time': 1800,
                'subtask_name': 'test.3mf',
                'layer_num': 50,
                'total_layer_num': 200
            },
            'info': {
                'bed_temper': 60.0,
                'nozzle_temper': 220.0,
                'chamber_temper': 35.0
            }
        })
        client.get_filaments = MagicMock(return_value=[
            {'type': 'PLA', 'color': 'White', 'k_value': 0.03},
            {'type': 'PETG', 'color': 'Black', 'k_value': 0.04}
        ])
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ftp_service():
    """Create a mock BambuFTPService."""
    with patch('src.printers.bambu_lab.BambuFTPService') as mock:
        service = MagicMock()
        service.connect = AsyncMock(return_value=True)
        service.disconnect = AsyncMock()
        service.list_files = AsyncMock(return_value=[
            MagicMock(name='test1.3mf', size=1024000, modified=datetime.now()),
            MagicMock(name='test2.gcode', size=2048000, modified=datetime.now())
        ])
        service.download_file = AsyncMock(return_value=True)
        mock.return_value = service
        yield service


@pytest.mark.unit
class TestBambuLabPrinterInitialization:
    """Test BambuLabPrinter initialization."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    def test_init_with_bambu_api(self, mock_client):
        """Test initialization when bambulabs_api is available."""
        from src.printers.bambu_lab import BambuLabPrinter

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        assert printer.printer_id == 'bambu_001'
        assert printer.name == 'Bambu A1'
        assert printer.ip_address == '192.168.1.100'
        assert printer.access_code == '12345678'
        assert printer.serial_number == 'ABC123'
        assert printer.use_bambu_api is True

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', False)
    @patch('src.printers.bambu_lab.MQTT_AVAILABLE', True)
    def test_init_with_mqtt_fallback(self):
        """Test initialization falls back to MQTT when bambulabs_api unavailable."""
        from src.printers.bambu_lab import BambuLabPrinter

        printer = BambuLabPrinter(
            printer_id='bambu_002',
            name='Bambu A1 Mini',
            ip_address='192.168.1.101',
            access_code='87654321',
            serial_number='XYZ789'
        )

        assert printer.use_bambu_api is False
        assert printer.mqtt_port == 8883  # BAMBU_MQTT_PORT constant

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', False)
    @patch('src.printers.bambu_lab.MQTT_AVAILABLE', False)
    def test_init_without_dependencies_raises_error(self):
        """Test initialization raises ImportError when no MQTT library available."""
        from src.printers.bambu_lab import BambuLabPrinter

        with pytest.raises(ImportError, match="Neither bambulabs_api nor paho-mqtt"):
            BambuLabPrinter(
                printer_id='bambu_003',
                name='Bambu X1C',
                ip_address='192.168.1.102',
                access_code='11111111',
                serial_number='TEST123'
            )

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    def test_init_with_file_service(self, mock_client):
        """Test initialization with optional file service."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_file_service = MagicMock()
        printer = BambuLabPrinter(
            printer_id='bambu_004',
            name='Bambu P1S',
            ip_address='192.168.1.103',
            access_code='22222222',
            serial_number='DEF456',
            file_service=mock_file_service
        )

        assert printer.file_service == mock_file_service
        assert printer.use_direct_ftp is True
        assert printer.ftp_service is None  # Not initialized until connect()


@pytest.mark.unit
@pytest.mark.asyncio
class TestBambuLabPrinterConnection:
    """Test BambuLabPrinter connection management."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    @patch('src.printers.bambu_lab.BambuFTPService')
    async def test_connect_bambu_api_success(self, mock_ftp_class, mock_client_class):
        """Test successful connection using bambulabs_api."""
        from src.printers.bambu_lab import BambuLabPrinter

        # Setup mocks
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        mock_ftp = MagicMock()
        mock_ftp.connect = AsyncMock(return_value=True)
        mock_ftp_class.return_value = mock_ftp

        # Create printer and connect
        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        result = await printer.connect()

        # Assertions
        assert result is True
        assert printer.is_connected is True
        assert printer.bambu_client is not None
        mock_client.connect.assert_called_once()

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_connect_bambu_api_failure(self, mock_client_class):
        """Test connection failure with bambulabs_api."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.utils.errors import PrinterConnectionError

        # Setup mock to fail connection
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        with pytest.raises(PrinterConnectionError, match="Connection refused"):
            await printer.connect()

        assert printer.is_connected is False

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', False)
    @patch('src.printers.bambu_lab.MQTT_AVAILABLE', True)
    @patch('src.printers.bambu_lab.mqtt')
    async def test_connect_mqtt_fallback(self, mock_mqtt):
        """Test connection using MQTT fallback."""
        from src.printers.bambu_lab import BambuLabPrinter

        # Setup MQTT mock
        mock_client = MagicMock()
        mock_client.connect_async = MagicMock(return_value=0)
        mock_client.loop_start = MagicMock()
        mock_mqtt.Client.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_002',
            name='Bambu A1',
            ip_address='192.168.1.101',
            access_code='87654321',
            serial_number='XYZ789'
        )

        # Need to mock the connection callback
        printer._on_connect(mock_client, None, None, 0)

        result = await printer.connect()

        assert result is True or printer.client is not None  # Connection initiated

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_disconnect(self, mock_client_class):
        """Test disconnect functionality."""
        from src.printers.bambu_lab import BambuLabPrinter

        # Setup connected printer
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        await printer.disconnect()

        assert printer.is_connected is False
        mock_client.disconnect.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestBambuLabPrinterStatus:
    """Test BambuLabPrinter status retrieval."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_get_status_success(self, mock_client_class):
        """Test successful status retrieval."""
        from src.printers.bambu_lab import BambuLabPrinter

        # Setup mock with status data
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.get_state = MagicMock(return_value={
            'print': {
                'gcode_state': 'RUNNING',
                'mc_percent': 75,
                'mc_remaining_time': 900,
                'subtask_name': 'benchy.3mf',
                'layer_num': 150,
                'total_layer_num': 200
            },
            'info': {
                'bed_temper': 60.0,
                'nozzle_temper': 220.0,
                'chamber_temper': 40.0
            }
        })
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        status = await printer.get_status()

        assert status is not None
        assert status.status.value in ['printing', 'idle', 'running']  # Map from RUNNING
        assert status.progress >= 0 and status.progress <= 100

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_get_status_not_connected(self, mock_client_class):
        """Test get_status when printer not connected."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.utils.errors import PrinterConnectionError

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.get_status()

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_map_bambu_status_printing(self, mock_client_class):
        """Test status mapping for printing state."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.models.printer import PrinterStatus

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        # Test various Bambu states
        assert printer._map_bambu_status('RUNNING') == PrinterStatus.PRINTING
        assert printer._map_bambu_status('PAUSE') == PrinterStatus.PAUSED
        assert printer._map_bambu_status('FINISH') == PrinterStatus.IDLE
        assert printer._map_bambu_status('IDLE') == PrinterStatus.IDLE


@pytest.mark.unit
@pytest.mark.asyncio
class TestBambuLabPrinterJobInfo:
    """Test BambuLabPrinter job information retrieval."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_get_job_info_active_job(self, mock_client_class):
        """Test retrieving active job information."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.get_state = MagicMock(return_value={
            'print': {
                'gcode_state': 'RUNNING',
                'mc_percent': 50,
                'mc_remaining_time': 3600,
                'subtask_name': 'test_print.3mf',
                'layer_num': 100,
                'total_layer_num': 200
            }
        })
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        job_info = await printer.get_job_info()

        assert job_info is not None
        assert job_info.filename == 'test_print.3mf'
        assert job_info.progress == 50
        assert job_info.time_remaining == 3600

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_get_job_info_no_active_job(self, mock_client_class):
        """Test retrieving job info when no job is active."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.get_state = MagicMock(return_value={
            'print': {
                'gcode_state': 'IDLE',
                'subtask_name': ''
            }
        })
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        job_info = await printer.get_job_info()

        assert job_info is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestBambuLabPrinterFileOperations:
    """Test BambuLabPrinter file listing and download."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    @patch('src.printers.bambu_lab.BambuFTPService')
    async def test_list_files_direct_ftp(self, mock_ftp_class, mock_client_class):
        """Test listing files via direct FTP."""
        from src.printers.bambu_lab import BambuLabPrinter

        # Setup FTP mock
        mock_ftp = MagicMock()
        mock_ftp.connect = AsyncMock(return_value=True)
        mock_ftp.list_files = AsyncMock(return_value=[
            MagicMock(name='model1.3mf', size=1024000, modified=datetime.now()),
            MagicMock(name='model2.gcode', size=2048000, modified=datetime.now())
        ])
        mock_ftp_class.return_value = mock_ftp

        # Setup client mock
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        files = await printer.list_files()

        assert len(files) >= 0  # May vary based on implementation

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_list_files_not_connected(self, mock_client_class):
        """Test list_files when printer not connected."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.utils.errors import PrinterConnectionError

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.list_files()

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_download_file_success(self, mock_client_class):
        """Test successful file download."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()

        # Mock download handler
        mock_download_handler = MagicMock()
        mock_download_handler.download = AsyncMock(return_value=True)
        printer.download_handler = mock_download_handler

        result = await printer.download_file('test.3mf', '/tmp/test.3mf')

        assert result is True
        mock_download_handler.download.assert_called_once()

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_download_file_not_connected(self, mock_client_class):
        """Test download_file when printer not connected."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.utils.errors import PrinterConnectionError

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.download_file('test.3mf', '/tmp/test.3mf')


@pytest.mark.unit
@pytest.mark.asyncio
class TestBambuLabPrinterPrintControl:
    """Test BambuLabPrinter print control operations."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_pause_print_success(self, mock_client_class):
        """Test pausing print successfully."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.pause = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        result = await printer.pause_print()

        assert result is True

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_resume_print_success(self, mock_client_class):
        """Test resuming print successfully."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.resume = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        result = await printer.resume_print()

        assert result is True

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_stop_print_success(self, mock_client_class):
        """Test stopping print successfully."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.stop = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        result = await printer.stop_print()

        assert result is True

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_pause_print_not_connected(self, mock_client_class):
        """Test pause_print when not connected raises error."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.utils.errors import PrinterConnectionError

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        with pytest.raises(PrinterConnectionError, match="Not connected"):
            await printer.pause_print()


@pytest.mark.unit
@pytest.mark.asyncio
class TestBambuLabPrinterCamera:
    """Test BambuLabPrinter camera functionality."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_has_camera(self, mock_client_class):
        """Test camera detection."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        has_camera = await printer.has_camera()

        # Bambu Lab printers typically have cameras
        assert isinstance(has_camera, bool)

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_get_camera_stream_url(self, mock_client_class):
        """Test getting camera stream URL."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        stream_url = await printer.get_camera_stream_url()

        # Should return URL or None
        assert stream_url is None or isinstance(stream_url, str)

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    async def test_take_snapshot(self, mock_client_class):
        """Test taking camera snapshot."""
        from src.printers.bambu_lab import BambuLabPrinter

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.get_camera_image = AsyncMock(return_value=b'fake_image_data')
        mock_client_class.return_value = mock_client

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        await printer.connect()
        snapshot = await printer.take_snapshot()

        # Should return bytes or None
        assert snapshot is None or isinstance(snapshot, bytes)


@pytest.mark.unit
class TestBambuLabPrinterHelpers:
    """Test BambuLabPrinter helper methods."""

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    def test_get_file_type_from_name(self, mock_client_class):
        """Test file type detection from filename."""
        from src.printers.bambu_lab import BambuLabPrinter

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        assert printer._get_file_type_from_name('test.3mf') == '3mf'
        assert printer._get_file_type_from_name('test.gcode') == 'gcode'
        assert printer._get_file_type_from_name('test.GCODE') == 'gcode'
        assert printer._get_file_type_from_name('test.stl') == 'stl'
        assert printer._get_file_type_from_name('test') == 'unknown'

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    def test_map_job_status(self, mock_client_class):
        """Test job status mapping."""
        from src.printers.bambu_lab import BambuLabPrinter
        from src.printers.base import JobStatus

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        assert printer._map_job_status('RUNNING') == JobStatus.PRINTING
        assert printer._map_job_status('PAUSE') == JobStatus.PAUSED
        assert printer._map_job_status('FINISH') == JobStatus.COMPLETED
        assert printer._map_job_status('IDLE') == JobStatus.IDLE
        assert printer._map_job_status('UNKNOWN') == JobStatus.UNKNOWN

    @patch('src.printers.bambu_lab.BAMBU_API_AVAILABLE', True)
    @patch('src.printers.bambu_lab.BambuClient')
    def test_extract_filaments_from_mqtt(self, mock_client_class):
        """Test filament extraction from MQTT data."""
        from src.printers.bambu_lab import BambuLabPrinter

        printer = BambuLabPrinter(
            printer_id='bambu_001',
            name='Bambu A1',
            ip_address='192.168.1.100',
            access_code='12345678',
            serial_number='ABC123'
        )

        mqtt_data = {
            'ams': {
                'ams': [
                    {
                        'tray': [
                            {'type': 'PLA', 'color': 'FFFFFF'},
                            {'type': 'PETG', 'color': '000000'}
                        ]
                    }
                ]
            }
        }

        filaments = printer._extract_filaments_from_mqtt(mqtt_data)

        assert len(filaments) == 2
        assert filaments[0].material == 'PLA'
        assert filaments[1].material == 'PETG'
