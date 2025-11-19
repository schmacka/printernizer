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
    async def test_add_printer_bambu_lab(self, printer_service, mock_database, mock_config_service):
        """Test adding a Bambu Lab printer."""
        from src.models.printer import PrinterType

        printer_id = str(uuid.uuid4())
        mock_database.create_printer.return_value = printer_id
        mock_config_service.add_printer.return_value = True
        mock_config_service.get_printer.return_value = None  # Simulate no instance created

        result = await printer_service.create_printer(
            name='Bambu Lab A1',
            printer_type=PrinterType.BAMBU_LAB,
            connection_config={
                'ip_address': '192.168.1.100',
                'access_code': '12345678',
                'serial_number': 'BAMBU001',
                'model': 'A1'
            }
        )

        assert result is not None
        assert isinstance(result, Printer)
        assert result.name == 'Bambu Lab A1'
        mock_config_service.add_printer.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_printer_prusa(self, printer_service, mock_database, mock_config_service):
        """Test adding a Prusa printer."""
        from src.models.printer import PrinterType

        printer_id = str(uuid.uuid4())
        mock_database.create_printer.return_value = printer_id
        mock_config_service.add_printer.return_value = True
        mock_config_service.get_printer.return_value = None  # Simulate no instance created

        result = await printer_service.create_printer(
            name='Prusa Core One',
            printer_type=PrinterType.PRUSA_CORE,
            connection_config={
                'ip_address': '192.168.1.101',
                'api_key': 'prusa_api_key_here',
                'model': 'Core One'
            }
        )

        assert result is not None
        assert isinstance(result, Printer)
        assert result.name == 'Prusa Core One'
        mock_config_service.add_printer.assert_called_once()

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
    async def test_remove_printer_deletes_record(self, printer_service, mock_config_service):
        """Test removing a printer."""
        printer_id = str(uuid.uuid4())
        mock_config_service.remove_printer.return_value = True

        result = await printer_service.delete_printer(printer_id)

        assert result == True
        mock_config_service.remove_printer.assert_called_once_with(printer_id)

    @pytest.mark.asyncio
    async def test_update_printer_name(self, printer_service, mock_config_service):
        """Test updating printer name."""
        from src.models.printer import PrinterType
        from src.services.config_service import PrinterConfig

        printer_id = str(uuid.uuid4())

        # Mock initial config
        initial_config = PrinterConfig(
            printer_id=printer_id,
            name='Old Name',
            type='bambu_lab',
            ip_address='192.168.1.100',
            access_code='12345678',
            is_active=True
        )

        # Mock updated config
        updated_config = PrinterConfig(
            printer_id=printer_id,
            name='New Name',
            type='bambu_lab',
            ip_address='192.168.1.100',
            access_code='12345678',
            is_active=True
        )

        mock_config_service.get_printer.side_effect = [initial_config, updated_config, updated_config]
        mock_config_service.add_printer.return_value = True

        result = await printer_service.update_printer(printer_id, name='New Name')

        assert result is not None
        assert isinstance(result, Printer)
        assert result.name == 'New Name'
        mock_config_service.add_printer.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_printer_by_id(self, printer_service):
        """Test retrieving a specific printer by ID."""
        printer_id = str(uuid.uuid4())

        # Create a mock printer instance with proper string attributes
        mock_printer_instance = MagicMock()
        mock_printer_instance.name = 'Test Printer'
        mock_printer_instance.ip_address = '192.168.1.100'
        mock_printer_instance.is_connected = True
        mock_printer_instance.last_status = None
        # Mock getattr to return None for optional fields
        mock_printer_instance.api_key = None
        mock_printer_instance.access_code = None
        mock_printer_instance.serial_number = None

        # Add it to printer_instances
        printer_service.connection.printer_instances[printer_id] = mock_printer_instance

        printer = await printer_service.get_printer(printer_id)

        assert printer is not None
        assert printer.id == printer_id
        assert isinstance(printer, Printer)
        assert printer.name == 'Test Printer'

    @pytest.mark.asyncio
    async def test_get_printer_by_id_not_found(self, printer_service):
        """Test retrieving non-existent printer returns None."""
        printer = await printer_service.get_printer('nonexistent_id')

        assert printer is None

    @pytest.mark.asyncio
    async def test_list_all_printers(self, printer_service):
        """Test listing all printers."""
        # Create mock printer instances with proper string attributes
        mock_printer1 = MagicMock()
        mock_printer1.name = 'Printer 1'
        mock_printer1.ip_address = '192.168.1.100'
        mock_printer1.is_connected = True
        mock_printer1.last_status = None
        mock_printer1.api_key = None
        mock_printer1.access_code = None
        mock_printer1.serial_number = None

        mock_printer2 = MagicMock()
        mock_printer2.name = 'Printer 2'
        mock_printer2.ip_address = '192.168.1.101'
        mock_printer2.is_connected = True
        mock_printer2.last_status = None
        mock_printer2.api_key = None
        mock_printer2.access_code = None
        mock_printer2.serial_number = None

        # Add to printer_instances
        printer_service.connection.printer_instances = {
            str(uuid.uuid4()): mock_printer1,
            str(uuid.uuid4()): mock_printer2,
        }

        printers = await printer_service.list_printers()

        assert len(printers) == 2
        assert all(isinstance(p, Printer) for p in printers)

    @pytest.mark.asyncio
    async def test_list_printers_by_type(self, printer_service):
        """Test filtering printers by type."""
        from src.models.printer import PrinterType

        # Create mock printer instances - the type is determined by checking class name
        mock_printer1 = MagicMock()
        mock_printer1.name = 'Bambu 1'
        mock_printer1.ip_address = '192.168.1.100'
        mock_printer1.is_connected = True
        mock_printer1.last_status = None
        mock_printer1.api_key = None
        mock_printer1.access_code = None
        mock_printer1.serial_number = None
        mock_printer1.__class__.__name__ = 'BambuLabPrinter'

        mock_printer2 = MagicMock()
        mock_printer2.name = 'Bambu 2'
        mock_printer2.ip_address = '192.168.1.101'
        mock_printer2.is_connected = True
        mock_printer2.last_status = None
        mock_printer2.api_key = None
        mock_printer2.access_code = None
        mock_printer2.serial_number = None
        mock_printer2.__class__.__name__ = 'BambuLabPrinter'

        # Add to printer_instances
        printer_service.connection.printer_instances = {
            str(uuid.uuid4()): mock_printer1,
            str(uuid.uuid4()): mock_printer2,
        }

        printers = await printer_service.list_printers()

        bambu_printers = [p for p in printers if p.type == PrinterType.BAMBU_LAB]
        assert len(bambu_printers) == 2

    @pytest.mark.asyncio
    async def test_list_printers_by_status(self, printer_service):
        """Test filtering printers by status."""
        from src.models.printer import PrinterStatus, PrinterStatusUpdate

        # Create mock printer instances with status
        mock_printer1 = MagicMock()
        mock_printer1.name = 'Printer 1'
        mock_printer1.ip_address = '192.168.1.100'
        mock_printer1.is_connected = True
        mock_printer1.api_key = None
        mock_printer1.access_code = None
        mock_printer1.serial_number = None
        mock_printer1.last_status = PrinterStatusUpdate(
            printer_id='p1',
            status=PrinterStatus.PRINTING,
            message='Printing',
            timestamp=datetime.now()
        )

        mock_printer2 = MagicMock()
        mock_printer2.name = 'Printer 2'
        mock_printer2.ip_address = '192.168.1.101'
        mock_printer2.is_connected = True
        mock_printer2.api_key = None
        mock_printer2.access_code = None
        mock_printer2.serial_number = None
        mock_printer2.last_status = PrinterStatusUpdate(
            printer_id='p2',
            status=PrinterStatus.PRINTING,
            message='Printing',
            timestamp=datetime.now()
        )

        mock_printer3 = MagicMock()
        mock_printer3.name = 'Printer 3'
        mock_printer3.ip_address = '192.168.1.102'
        mock_printer3.is_connected = True
        mock_printer3.api_key = None
        mock_printer3.access_code = None
        mock_printer3.serial_number = None
        mock_printer3.last_status = PrinterStatusUpdate(
            printer_id='p3',
            status=PrinterStatus.ONLINE,
            message='Idle',
            timestamp=datetime.now()
        )

        # Add to printer_instances
        printer_service.connection.printer_instances = {
            'p1': mock_printer1,
            'p2': mock_printer2,
            'p3': mock_printer3,
        }

        printers = await printer_service.list_printers()

        printing_printers = [p for p in printers if p.status == PrinterStatus.PRINTING]
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
        from src.models.printer import PrinterStatus, PrinterStatusUpdate

        printer_id = str(uuid.uuid4())

        # Create mock printer instance
        mock_printer_instance = MagicMock()
        mock_printer_instance.is_connected = True
        mock_printer_instance.get_status = AsyncMock(return_value=PrinterStatusUpdate(
            printer_id=printer_id,
            status=PrinterStatus.PRINTING,
            message='Printing test.3mf',
            temperature_bed=60.0,
            temperature_nozzle=210.0,
            progress=50,
            current_job='test.3mf',
            timestamp=datetime.now()
        ))

        # Add to printer_instances
        printer_service.connection.printer_instances[printer_id] = mock_printer_instance

        # Mock database update
        mock_database.update_printer_status = AsyncMock()

        status = await printer_service.get_printer_status(printer_id)

        assert status is not None
        assert 'status' in status
        assert status['status'] == 'printing'  # Enum values are lowercase
        assert status['progress'] == 50

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
        printer_service.monitoring.monitoring_active = True

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
    async def test_get_printer_files(self, printer_service):
        """Test retrieving files from a printer."""
        from src.printers.base import PrinterFile

        printer_id = str(uuid.uuid4())

        # Mock printer instance with list_files method (not get_files)
        mock_printer_instance = MagicMock()
        mock_printer_instance.is_connected = True
        mock_printer_instance.list_files = AsyncMock(return_value=[
            PrinterFile(filename='test.3mf', size=1024, modified=datetime.now(), path='/test.3mf')
        ])

        # Add to printer_instances
        printer_service.connection.printer_instances[printer_id] = mock_printer_instance

        files = await printer_service.get_printer_files(printer_id)

        assert isinstance(files, list)
        assert len(files) == 1
        assert files[0]['filename'] == 'test.3mf'

    @pytest.mark.asyncio
    async def test_download_printer_file(self, printer_service):
        """Test downloading a file from a printer."""
        printer_id = str(uuid.uuid4())
        filename = 'test.3mf'

        # Mock printer instance
        mock_printer_instance = MagicMock()
        mock_printer_instance.is_connected = True
        mock_printer_instance.download_file = AsyncMock(return_value=True)  # Returns bool, not path

        # Add to printer_instances
        printer_service.connection.printer_instances[printer_id] = mock_printer_instance

        result = await printer_service.download_printer_file(printer_id, filename, '/tmp/test.3mf')

        assert result is True
        mock_printer_instance.download_file.assert_called_once_with(filename, '/tmp/test.3mf')


class TestPrinterValidation:
    """Test printer validation and error handling."""

    @pytest.mark.asyncio
    async def test_add_printer_generates_unique_id(self, printer_service, mock_database, mock_config_service):
        """Test that printer creation generates unique IDs."""
        from src.models.printer import PrinterType

        printer_id = str(uuid.uuid4())
        mock_database.create_printer.return_value = printer_id
        mock_config_service.add_printer.return_value = True
        mock_config_service.get_printer.return_value = None  # Simulate no instance created

        result = await printer_service.create_printer(
            name='Test Printer',
            printer_type=PrinterType.BAMBU_LAB,
            connection_config={
                'ip_address': '192.168.1.100',
                'access_code': '12345678'
            }
        )

        assert result is not None
        assert isinstance(result, Printer)
        assert result.id is not None  # ID should be generated

    @pytest.mark.asyncio
    async def test_remove_printer_not_found(self, printer_service, mock_config_service):
        """Test removing non-existent printer."""
        mock_config_service.remove_printer.return_value = False

        result = await printer_service.delete_printer('nonexistent_id')

        assert result == False

    @pytest.mark.asyncio
    async def test_get_printer_status_not_found(self, printer_service):
        """Test getting status of non-existent printer."""
        from src.utils.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
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
