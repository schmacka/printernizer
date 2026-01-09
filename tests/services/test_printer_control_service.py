"""
Unit tests for PrinterControlService.

Tests the printer control service functionality including:
- Initialization and configuration
- Print job control (pause/resume/stop)
- Printer monitoring control (start/stop)
- Event emissions for control actions
- Error handling and edge cases
- Printer instance retrieval
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime


@pytest.fixture
def event_service():
    """Create a mock EventService."""
    service = MagicMock()
    service.emit_event = AsyncMock()
    return service


@pytest.fixture
def mock_printer_instance():
    """Create a mock printer instance."""
    printer = MagicMock()
    printer.printer_id = 'test_printer_001'
    printer.name = 'Test Printer'
    printer.is_connected = True
    printer.connect = AsyncMock(return_value=True)
    printer.pause_print = AsyncMock(return_value=True)
    printer.resume_print = AsyncMock(return_value=True)
    printer.stop_print = AsyncMock(return_value=True)
    return printer


@pytest.fixture
def connection_service(mock_printer_instance):
    """Create a mock connection service."""
    service = MagicMock()
    # Mock get_printer_instance method - this is what the service actually calls
    service.get_printer_instance = MagicMock(return_value=mock_printer_instance)
    # Keep printer_instances dict for backward compatibility with some tests
    service.printer_instances = {
        'test_printer_001': mock_printer_instance
    }
    service.start_monitoring_for_printer = AsyncMock(return_value=True)
    service.stop_monitoring_for_printer = AsyncMock(return_value=True)
    return service


@pytest.mark.unit
class TestPrinterControlServiceInitialization:
    """Test PrinterControlService initialization."""

    def test_init_with_connection_service(self, event_service, connection_service):
        """Test initialization with connection service."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        assert service.event_service == event_service
        assert service.connection_service == connection_service

    def test_init_without_connection_service(self, event_service):
        """Test initialization without connection service."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=None
        )

        assert service.event_service == event_service
        assert service.connection_service is None

    def test_set_connection_service(self, event_service, connection_service):
        """Test setting connection service after initialization."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=None
        )

        assert service.connection_service is None

        service.set_connection_service(connection_service)

        assert service.connection_service == connection_service


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrinterControlServicePauseOperations:
    """Test PrinterControlService pause operations."""

    async def test_pause_printer_success(self, event_service, connection_service, mock_printer_instance):
        """Test successful print pause."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.pause_printer('test_printer_001')

        assert result is True
        mock_printer_instance.pause_print.assert_called_once()
        event_service.emit_event.assert_called_once()
        call_args = event_service.emit_event.call_args[0]
        assert call_args[0] == 'print_paused'
        assert call_args[1]['printer_id'] == 'test_printer_001'

    async def test_pause_printer_not_connected(self, event_service, connection_service, mock_printer_instance):
        """Test pause when printer not connected triggers connection."""
        from src.services.printer_control_service import PrinterControlService

        # Setup printer as not connected
        mock_printer_instance.is_connected = False

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.pause_printer('test_printer_001')

        assert result is True
        mock_printer_instance.connect.assert_called_once()
        mock_printer_instance.pause_print.assert_called_once()

    async def test_pause_printer_not_found(self, event_service):
        """Test pause when printer not found raises error."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        # Connection service that returns None for unknown printers
        empty_connection_service = MagicMock()
        empty_connection_service.get_printer_instance = MagicMock(return_value=None)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=empty_connection_service
        )

        with pytest.raises(NotFoundError, match="Printer not found: unknown_printer"):
            await service.pause_printer('unknown_printer')

    async def test_pause_printer_command_fails(self, event_service, connection_service, mock_printer_instance):
        """Test pause when printer command fails."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import PrinterConnectionError

        # Setup pause to fail
        mock_printer_instance.pause_print = AsyncMock(side_effect=Exception("Pause failed"))

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        with pytest.raises(PrinterConnectionError, match="Pause failed"):
            await service.pause_printer('test_printer_001')

        # Event should not be emitted on failure
        event_service.emit_event.assert_not_called()

    async def test_pause_printer_returns_false(self, event_service, connection_service, mock_printer_instance):
        """Test pause when printer returns False (pause not accepted)."""
        from src.services.printer_control_service import PrinterControlService

        # Setup pause to return False
        mock_printer_instance.pause_print = AsyncMock(return_value=False)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.pause_printer('test_printer_001')

        assert result is False
        # Event should not be emitted when pause unsuccessful
        event_service.emit_event.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrinterControlServiceResumeOperations:
    """Test PrinterControlService resume operations."""

    async def test_resume_printer_success(self, event_service, connection_service, mock_printer_instance):
        """Test successful print resume."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.resume_printer('test_printer_001')

        assert result is True
        mock_printer_instance.resume_print.assert_called_once()
        event_service.emit_event.assert_called_once()
        call_args = event_service.emit_event.call_args[0]
        assert call_args[0] == 'print_resumed'
        assert call_args[1]['printer_id'] == 'test_printer_001'

    async def test_resume_printer_not_connected(self, event_service, connection_service, mock_printer_instance):
        """Test resume when printer not connected triggers connection."""
        from src.services.printer_control_service import PrinterControlService

        # Setup printer as not connected
        mock_printer_instance.is_connected = False

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.resume_printer('test_printer_001')

        assert result is True
        mock_printer_instance.connect.assert_called_once()
        mock_printer_instance.resume_print.assert_called_once()

    async def test_resume_printer_not_found(self, event_service):
        """Test resume when printer not found raises error."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        empty_connection_service = MagicMock()
        empty_connection_service.get_printer_instance = MagicMock(return_value=None)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=empty_connection_service
        )

        with pytest.raises(NotFoundError, match="Printer not found: unknown_printer"):
            await service.resume_printer('unknown_printer')

    async def test_resume_printer_command_fails(self, event_service, connection_service, mock_printer_instance):
        """Test resume when printer command fails."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import PrinterConnectionError

        # Setup resume to fail
        mock_printer_instance.resume_print = AsyncMock(side_effect=Exception("Resume failed"))

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        with pytest.raises(PrinterConnectionError, match="Resume failed"):
            await service.resume_printer('test_printer_001')

        event_service.emit_event.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrinterControlServiceStopOperations:
    """Test PrinterControlService stop operations."""

    async def test_stop_printer_success(self, event_service, connection_service, mock_printer_instance):
        """Test successful print stop."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.stop_printer('test_printer_001')

        assert result is True
        mock_printer_instance.stop_print.assert_called_once()
        event_service.emit_event.assert_called_once()
        call_args = event_service.emit_event.call_args[0]
        assert call_args[0] == 'print_stopped'
        assert call_args[1]['printer_id'] == 'test_printer_001'

    async def test_stop_printer_not_connected(self, event_service, connection_service, mock_printer_instance):
        """Test stop when printer not connected triggers connection."""
        from src.services.printer_control_service import PrinterControlService

        # Setup printer as not connected
        mock_printer_instance.is_connected = False

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.stop_printer('test_printer_001')

        assert result is True
        mock_printer_instance.connect.assert_called_once()
        mock_printer_instance.stop_print.assert_called_once()

    async def test_stop_printer_not_found(self, event_service):
        """Test stop when printer not found raises error."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        empty_connection_service = MagicMock()
        empty_connection_service.get_printer_instance = MagicMock(return_value=None)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=empty_connection_service
        )

        with pytest.raises(NotFoundError, match="Printer not found: unknown_printer"):
            await service.stop_printer('unknown_printer')

    async def test_stop_printer_command_fails(self, event_service, connection_service, mock_printer_instance):
        """Test stop when printer command fails."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import PrinterConnectionError

        # Setup stop to fail
        mock_printer_instance.stop_print = AsyncMock(side_effect=Exception("Stop failed"))

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        with pytest.raises(PrinterConnectionError, match="Stop failed"):
            await service.stop_printer('test_printer_001')

        event_service.emit_event.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrinterControlServiceMonitoringOperations:
    """Test PrinterControlService monitoring control operations."""

    async def test_start_printer_monitoring_success(self, event_service, connection_service, mock_printer_instance):
        """Test successful monitoring start."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.start_printer_monitoring('test_printer_001')

        assert result is True
        # The implementation ensures printer is connected (if not already)
        # Since mock_printer_instance.is_connected is True, connect should not be called
        connection_service.get_printer_instance.assert_called_once_with('test_printer_001')

    async def test_start_printer_monitoring_not_found(self, event_service):
        """Test start monitoring when printer not found."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        empty_connection_service = MagicMock()
        empty_connection_service.get_printer_instance = MagicMock(return_value=None)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=empty_connection_service
        )

        with pytest.raises(NotFoundError, match="Printer not found: unknown_printer"):
            await service.start_printer_monitoring('unknown_printer')

    async def test_start_printer_monitoring_fails(self, event_service, connection_service, mock_printer_instance):
        """Test start monitoring when operation fails."""
        from src.services.printer_control_service import PrinterControlService

        # Setup printer as not connected and connect to fail
        mock_printer_instance.is_connected = False
        mock_printer_instance.connect = AsyncMock(side_effect=Exception("Connection failed"))

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        # The implementation catches exceptions and returns False
        result = await service.start_printer_monitoring('test_printer_001')
        assert result is False

    async def test_stop_printer_monitoring_success(self, event_service, connection_service, mock_printer_instance):
        """Test successful monitoring stop."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        result = await service.stop_printer_monitoring('test_printer_001')

        assert result is True
        # The implementation just verifies the printer exists and logs
        connection_service.get_printer_instance.assert_called_once_with('test_printer_001')

    async def test_stop_printer_monitoring_not_found(self, event_service):
        """Test stop monitoring when printer not found."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        empty_connection_service = MagicMock()
        empty_connection_service.get_printer_instance = MagicMock(return_value=None)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=empty_connection_service
        )

        with pytest.raises(NotFoundError, match="Printer not found: unknown_printer"):
            await service.stop_printer_monitoring('unknown_printer')

    async def test_stop_printer_monitoring_when_not_connected(self, event_service, connection_service, mock_printer_instance):
        """Test stop monitoring when printer not connected still succeeds."""
        from src.services.printer_control_service import PrinterControlService

        # Setup printer as not connected
        mock_printer_instance.is_connected = False

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        # Stop monitoring should still succeed (it's a no-op in current implementation)
        result = await service.stop_printer_monitoring('test_printer_001')
        assert result is True


@pytest.mark.unit
class TestPrinterControlServiceHelpers:
    """Test PrinterControlService helper methods."""

    def test_get_printer_instance_success(self, event_service, connection_service, mock_printer_instance):
        """Test successful printer instance retrieval."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        instance = service._get_printer_instance('test_printer_001')

        assert instance == mock_printer_instance

    def test_get_printer_instance_not_found(self, event_service):
        """Test printer instance retrieval when printer not found."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        # Create connection service that returns None for unknown printers
        connection_svc = MagicMock()
        connection_svc.get_printer_instance = MagicMock(return_value=None)

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_svc
        )

        with pytest.raises(NotFoundError, match="Printer not found: unknown_printer"):
            service._get_printer_instance('unknown_printer')

    def test_get_printer_instance_no_connection_service(self, event_service):
        """Test printer instance retrieval when no connection service."""
        from src.services.printer_control_service import PrinterControlService
        from src.utils.errors import NotFoundError

        service = PrinterControlService(
            event_service=event_service,
            connection_service=None
        )

        # When no connection service is set, printer is not found
        with pytest.raises(NotFoundError, match="Printer not found: test_printer_001"):
            service._get_printer_instance('test_printer_001')


@pytest.mark.unit
@pytest.mark.asyncio
class TestPrinterControlServiceEventEmissions:
    """Test PrinterControlService event emissions."""

    async def test_pause_emits_correct_event_data(self, event_service, connection_service, mock_printer_instance):
        """Test pause emits event with correct data structure."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        await service.pause_printer('test_printer_001')

        call_args = event_service.emit_event.call_args[0]
        event_data = call_args[1]

        assert 'printer_id' in event_data
        assert 'timestamp' in event_data
        assert event_data['printer_id'] == 'test_printer_001'
        # Verify timestamp is ISO format
        datetime.fromisoformat(event_data['timestamp'])

    async def test_resume_emits_correct_event_data(self, event_service, connection_service, mock_printer_instance):
        """Test resume emits event with correct data structure."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        await service.resume_printer('test_printer_001')

        call_args = event_service.emit_event.call_args[0]
        event_data = call_args[1]

        assert 'printer_id' in event_data
        assert 'timestamp' in event_data
        assert event_data['printer_id'] == 'test_printer_001'

    async def test_stop_emits_correct_event_data(self, event_service, connection_service, mock_printer_instance):
        """Test stop emits event with correct data structure."""
        from src.services.printer_control_service import PrinterControlService

        service = PrinterControlService(
            event_service=event_service,
            connection_service=connection_service
        )

        await service.stop_printer('test_printer_001')

        call_args = event_service.emit_event.call_args[0]
        event_data = call_args[1]

        assert 'printer_id' in event_data
        assert 'timestamp' in event_data
        assert event_data['printer_id'] == 'test_printer_001'
