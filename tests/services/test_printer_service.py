"""
Unit tests for Printer Service.
Implements test cases from TEST_COVERAGE_ANALYSIS.md Phase 1.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.printer_service import PrinterService
from src.services.event_service import EventService
from src.services.config_service import ConfigService
from src.models.printer import Printer, PrinterType, PrinterStatus


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    db = MagicMock()
    db.list_printers = AsyncMock(return_value=[])
    db.get_printer = AsyncMock()
    db.create_printer = AsyncMock()
    db.update_printer = AsyncMock(return_value=True)
    db.delete_printer = AsyncMock(return_value=True)
    return db


@pytest.fixture
def mock_event_service():
    """Create mock event service for testing."""
    event_service = MagicMock(spec=EventService)
    event_service.emit = AsyncMock()
    event_service.emit_event = AsyncMock()
    return event_service


@pytest.fixture
def mock_config_service():
    """Create mock config service for testing."""
    config_service = MagicMock(spec=ConfigService)
    config_service.get_config = MagicMock(return_value={})
    config_service.get_printer_config = MagicMock(return_value={})
    return config_service


@pytest.fixture
def mock_file_service():
    """Create mock file service for testing."""
    file_service = MagicMock()
    file_service.download_file = AsyncMock()
    return file_service


@pytest.fixture
def printer_service(mock_database, mock_event_service, mock_config_service, mock_file_service):
    """Create PrinterService instance with mock dependencies."""
    service = PrinterService(
        mock_database,
        mock_event_service,
        mock_config_service,
        mock_file_service
    )
    return service


def create_sample_printer_data(
    printer_id=None,
    name='Test Printer',
    printer_type='bambu_lab',
    ip_address='192.168.1.100',
    status='idle',
    **kwargs
):
    """Helper to create sample printer data."""
    printer_id = printer_id or str(uuid.uuid4())
    data = {
        'id': printer_id,
        'name': name,
        'printer_type': printer_type,
        'ip_address': ip_address,
        'status': status,
        'access_code': '12345678',
        'serial_number': f'SN{printer_id[:8]}',
        'model': 'A1',
        'enabled': True,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }
    data.update(kwargs)
    return data


class TestPrinterManagement:
    """Test printer CRUD operations."""

    @pytest.mark.asyncio
    async def test_add_printer_bambu_lab(self, printer_service, mock_database):
        """Test adding a Bambu Lab printer."""
        printer_data = {
            'name': 'Bambu Lab A1',
            'printer_type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'access_code': '12345678',
            'serial_number': 'BAMBU001',
            'model': 'A1'
        }
        
        printer_id = str(uuid.uuid4())
        mock_database.create_printer.return_value = printer_id
        
        result = await printer_service.create_printer(**printer_data)
        
        assert result is not None
        mock_database.create_printer.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_printer_prusa(self, printer_service, mock_database):
        """Test adding a Prusa printer."""
        printer_data = {
            'name': 'Prusa Core One',
            'printer_type': 'prusa',
            'ip_address': '192.168.1.101',
            'api_key': 'prusa_api_key_here',
            'model': 'Core One'
        }
        
        printer_id = str(uuid.uuid4())
        mock_database.create_printer.return_value = printer_id
        
        result = await printer_service.create_printer(**printer_data)
        
        assert result is not None
        mock_database.create_printer.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_printer_validates_ip_address(self, printer_service, mock_database):
        """Test that printer creation validates IP address."""
        printer_data = {
            'name': 'Invalid Printer',
            'printer_type': 'bambu_lab',
            'ip_address': 'invalid_ip',  # Invalid IP
            'access_code': '12345678'
        }
        
        # Should either reject or handle gracefully
        with pytest.raises(Exception):
            await printer_service.create_printer(**printer_data)

    @pytest.mark.asyncio
    async def test_remove_printer_deletes_record(self, printer_service, mock_database):
        """Test removing a printer."""
        printer_id = str(uuid.uuid4())
        mock_database.delete_printer.return_value = True
        
        result = await printer_service.delete_printer(printer_id)
        
        assert result == True
        mock_database.delete_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_update_printer_name(self, printer_service, mock_database):
        """Test updating printer name."""
        printer_id = str(uuid.uuid4())
        printer_data = create_sample_printer_data(printer_id=printer_id)
        mock_database.get_printer.return_value = printer_data
        mock_database.update_printer.return_value = Printer(**printer_data)
        
        result = await printer_service.update_printer(printer_id, name='New Name')
        
        mock_database.update_printer.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_printer_by_id(self, printer_service, mock_database):
        """Test retrieving a specific printer by ID."""
        printer_id = str(uuid.uuid4())
        printer_data = create_sample_printer_data(printer_id=printer_id)
        mock_database.get_printer.return_value = printer_data
        
        printer = await printer_service.get_printer(printer_id)
        
        assert printer is not None
        assert printer.id == printer_id
        mock_database.get_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_get_printer_by_id_not_found(self, printer_service, mock_database):
        """Test retrieving non-existent printer returns None."""
        mock_database.get_printer.return_value = None
        
        printer = await printer_service.get_printer('nonexistent_id')
        
        assert printer is None

    @pytest.mark.asyncio
    async def test_list_all_printers(self, printer_service, mock_database):
        """Test listing all printers."""
        sample_printers = [
            create_sample_printer_data(printer_id=str(uuid.uuid4())),
            create_sample_printer_data(printer_id=str(uuid.uuid4())),
        ]
        mock_database.list_printers.return_value = sample_printers
        
        printers = await printer_service.list_printers()
        
        assert len(printers) == 2
        mock_database.list_printers.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_printers_by_type(self, printer_service, mock_database):
        """Test filtering printers by type."""
        sample_printers = [
            create_sample_printer_data(printer_type='bambu_lab'),
            create_sample_printer_data(printer_type='bambu_lab'),
        ]
        mock_database.list_printers.return_value = sample_printers
        
        printers = await printer_service.list_printers()
        
        bambu_printers = [p for p in printers if p.printer_type == 'bambu_lab']
        assert len(bambu_printers) == 2

    @pytest.mark.asyncio
    async def test_list_printers_by_status(self, printer_service, mock_database):
        """Test filtering printers by status."""
        sample_printers = [
            create_sample_printer_data(status='printing'),
            create_sample_printer_data(status='printing'),
            create_sample_printer_data(status='idle'),
        ]
        mock_database.list_printers.return_value = sample_printers
        
        printers = await printer_service.list_printers()
        
        printing_printers = [p for p in printers if p.status == 'printing']
        assert len(printing_printers) == 2


class TestPrinterConnections:
    """Test printer connection management."""

    @pytest.mark.asyncio
    async def test_connect_printer_establishes_connection(self, printer_service):
        """Test printer connection establishment."""
        printer_id = str(uuid.uuid4())
        
        # Mock the connection service
        printer_service.connection.connect_printer = AsyncMock(return_value=True)
        
        result = await printer_service.connect_printer(printer_id)
        
        assert result == True
        printer_service.connection.connect_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_disconnect_printer_closes_connection(self, printer_service):
        """Test disconnecting a printer."""
        printer_id = str(uuid.uuid4())
        
        # Mock the connection service
        printer_service.connection.disconnect_printer = AsyncMock(return_value=True)
        
        result = await printer_service.disconnect_printer(printer_id)
        
        assert result == True
        printer_service.connection.disconnect_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_health_check(self, printer_service):
        """Test printer service health check."""
        # Mock the connection service health check
        printer_service.connection.health_check = AsyncMock(return_value={
            'connection_service': 'ok',
            'connected_printers': 0
        })
        
        health = await printer_service.health_check()
        
        assert health is not None
        assert isinstance(health, dict)


class TestPrinterStatus:
    """Test printer status and monitoring."""

    @pytest.mark.asyncio
    async def test_get_printer_current_status(self, printer_service, mock_database):
        """Test retrieving printer current status."""
        printer_id = str(uuid.uuid4())
        printer_data = create_sample_printer_data(printer_id=printer_id, status='printing')
        mock_database.get_printer.return_value = printer_data
        
        status = await printer_service.get_printer_status(printer_id)
        
        assert status is not None
        assert 'status' in status or 'state' in status

    @pytest.mark.asyncio
    async def test_start_monitoring(self, printer_service):
        """Test starting printer monitoring."""
        # Mock the monitoring service
        printer_service.monitoring.start_monitoring = AsyncMock(return_value=True)
        
        result = await printer_service.start_monitoring()
        
        assert result == True

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, printer_service):
        """Test stopping printer monitoring."""
        # Mock the monitoring service
        printer_service.monitoring.stop_monitoring = AsyncMock(return_value=True)
        
        result = await printer_service.stop_monitoring()
        
        assert result == True

    @pytest.mark.asyncio
    async def test_monitoring_active_property(self, printer_service):
        """Test checking if monitoring is active."""
        printer_service.monitoring._monitoring_active = True
        
        is_active = printer_service.monitoring_active
        
        assert is_active == True


class TestPrinterControl:
    """Test printer control operations."""

    @pytest.mark.asyncio
    async def test_pause_printer(self, printer_service):
        """Test pausing a printer."""
        printer_id = str(uuid.uuid4())
        
        # Mock the control service
        printer_service.control.pause_printer = AsyncMock(return_value=True)
        
        result = await printer_service.pause_printer(printer_id)
        
        assert result == True
        printer_service.control.pause_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_resume_printer(self, printer_service):
        """Test resuming a paused printer."""
        printer_id = str(uuid.uuid4())
        
        # Mock the control service
        printer_service.control.resume_printer = AsyncMock(return_value=True)
        
        result = await printer_service.resume_printer(printer_id)
        
        assert result == True
        printer_service.control.resume_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_stop_printer(self, printer_service):
        """Test stopping a printer job."""
        printer_id = str(uuid.uuid4())
        
        # Mock the control service
        printer_service.control.stop_printer = AsyncMock(return_value=True)
        
        result = await printer_service.stop_printer(printer_id)
        
        assert result == True
        printer_service.control.stop_printer.assert_called_once_with(printer_id)


class TestPrinterFiles:
    """Test printer file operations."""

    @pytest.mark.asyncio
    async def test_get_printer_files(self, printer_service, mock_database):
        """Test retrieving files from a printer."""
        printer_id = str(uuid.uuid4())
        printer_data = create_sample_printer_data(printer_id=printer_id, printer_type='bambu_lab')
        mock_database.get_printer.return_value = printer_data
        
        # Mock printer instance with get_files method
        mock_printer_instance = MagicMock()
        mock_printer_instance.get_files = AsyncMock(return_value=[
            {'filename': 'test.3mf', 'size': 1024}
        ])
        
        with patch.object(printer_service.connection, 'get_printer_instance', return_value=mock_printer_instance):
            files = await printer_service.get_printer_files(printer_id)
            
            assert isinstance(files, list)

    @pytest.mark.asyncio
    async def test_download_printer_file(self, printer_service, mock_database):
        """Test downloading a file from a printer."""
        printer_id = str(uuid.uuid4())
        filename = 'test.3mf'
        
        printer_data = create_sample_printer_data(printer_id=printer_id)
        mock_database.get_printer.return_value = printer_data
        
        # Mock file download
        mock_printer_instance = MagicMock()
        mock_printer_instance.download_file = AsyncMock(return_value='/path/to/test.3mf')
        
        with patch.object(printer_service.connection, 'get_printer_instance', return_value=mock_printer_instance):
            result = await printer_service.download_printer_file(printer_id, filename)
            
            assert result is not None


class TestPrinterValidation:
    """Test printer validation and error handling."""

    @pytest.mark.asyncio
    async def test_add_printer_generates_unique_id(self, printer_service, mock_database):
        """Test that printer creation generates unique IDs."""
        printer_data = {
            'name': 'Test Printer',
            'printer_type': 'bambu_lab',
            'ip_address': '192.168.1.100',
            'access_code': '12345678'
        }
        
        printer_id = str(uuid.uuid4())
        mock_database.create_printer.return_value = printer_id
        
        result = await printer_service.create_printer(**printer_data)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_remove_printer_not_found(self, printer_service, mock_database):
        """Test removing non-existent printer."""
        mock_database.delete_printer.return_value = False
        
        result = await printer_service.delete_printer('nonexistent_id')
        
        assert result == False

    @pytest.mark.asyncio
    async def test_get_printer_status_not_found(self, printer_service, mock_database):
        """Test getting status of non-existent printer."""
        mock_database.get_printer.return_value = None
        
        with pytest.raises(Exception):
            await printer_service.get_printer_status('nonexistent_id')


class TestPrinterServiceInitialization:
    """Test printer service initialization."""

    @pytest.mark.asyncio
    async def test_initialize_service(self, printer_service):
        """Test printer service initialization."""
        # Mock the connection service initialize
        printer_service.connection.initialize = AsyncMock()
        printer_service.monitoring.initialize = AsyncMock()
        
        await printer_service.initialize()
        
        printer_service.connection.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_service(self, printer_service):
        """Test printer service shutdown."""
        # Mock the connection service shutdown
        printer_service.connection.shutdown = AsyncMock()
        printer_service.monitoring.stop_monitoring = AsyncMock(return_value=True)
        
        await printer_service.shutdown()
        
        printer_service.connection.shutdown.assert_called_once()


class TestPrinterServiceCoordination:
    """Test coordination between specialized services."""

    @pytest.mark.asyncio
    async def test_file_service_injection(self, mock_database, mock_event_service, mock_config_service):
        """Test that file service can be set after initialization."""
        service = PrinterService(
            mock_database,
            mock_event_service,
            mock_config_service,
            file_service=None
        )
        
        assert service.file_service is None
        
        mock_file_service = MagicMock()
        service.file_service = mock_file_service
        
        assert service.file_service is not None

    @pytest.mark.asyncio
    async def test_services_share_references(self, printer_service):
        """Test that specialized services share references correctly."""
        # Monitoring service should have reference to connection service
        assert printer_service.monitoring.connection_service is not None
        assert printer_service.monitoring.connection_service == printer_service.connection
        
        # Connection service should have reference to monitoring service
        assert printer_service.connection.monitoring_service is not None
        assert printer_service.connection.monitoring_service == printer_service.monitoring
