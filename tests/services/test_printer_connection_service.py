"""
Unit tests for PrinterConnectionService.

Tests the printer connection management functionality including:
- Printer initialization and instance creation
- Connection/disconnection management
- Health checks
- Database synchronization
- Event emissions
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialization(async_database, event_service):
    """Test service initialization."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service to return empty printer configs
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    # Act
    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )
    await conn_service.initialize()

    # Assert
    assert len(conn_service.printer_instances) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_load_bambu_lab_printer(async_database, event_service):
    """Test loading Bambu Lab printer configuration."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()

    # Mock printer config
    mock_config = MagicMock()
    mock_config.type = "bambu_lab"
    mock_config.name = "Bambu A1"
    mock_config.ip_address = "192.168.1.100"
    mock_config.access_code = "12345678"
    mock_config.serial_number = "ABC123"

    mock_config_service.get_active_printers = MagicMock(return_value={
        "bambu_001": mock_config
    })

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Act
    await conn_service.initialize()

    # Assert
    assert len(conn_service.printer_instances) == 1
    assert "bambu_001" in conn_service.printer_instances
    instance = conn_service.printer_instances["bambu_001"]
    assert instance.name == "Bambu A1"
    assert instance.ip_address == "192.168.1.100"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_load_prusa_printer(async_database, event_service):
    """Test loading Prusa printer configuration."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()

    # Mock printer config
    mock_config = MagicMock()
    mock_config.type = "prusa_core"
    mock_config.name = "Prusa Core One"
    mock_config.ip_address = "192.168.1.101"
    mock_config.api_key = "test_api_key_12345"

    mock_config_service.get_active_printers = MagicMock(return_value={
        "prusa_001": mock_config
    })

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Act
    await conn_service.initialize()

    # Assert
    assert len(conn_service.printer_instances) == 1
    assert "prusa_001" in conn_service.printer_instances
    instance = conn_service.printer_instances["prusa_001"]
    assert instance.name == "Prusa Core One"
    assert instance.ip_address == "192.168.1.101"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_load_unknown_printer_type(async_database, event_service):
    """Test loading unknown printer type (should be skipped)."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()

    # Mock unknown printer config
    mock_config = MagicMock()
    mock_config.type = "unknown_type"
    mock_config.name = "Unknown Printer"
    mock_config.ip_address = "192.168.1.200"

    mock_config_service.get_active_printers = MagicMock(return_value={
        "unknown_001": mock_config
    })

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Act
    await conn_service.initialize()

    # Assert - unknown type should not create instance
    assert len(conn_service.printer_instances) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_printer_success(async_database, event_service):
    """Test successful printer connection."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer instance
    mock_printer = AsyncMock()
    mock_printer.name = "Test Printer"
    mock_printer.connect = AsyncMock(return_value=True)
    conn_service.printer_instances["test_001"] = mock_printer

    # Mock database method
    async_database.update_printer_status = AsyncMock()

    # Track events
    events_emitted = []
    async def capture_event(event_type, data):
        events_emitted.append({"type": event_type, "data": data})
    event_service.emit_event = capture_event

    # Act
    result = await conn_service.connect_printer("test_001")

    # Assert
    assert result is True
    mock_printer.connect.assert_called_once()

    # Verify event emitted
    assert len(events_emitted) == 1
    assert events_emitted[0]["type"] == "printer_connected"
    assert events_emitted[0]["data"]["printer_id"] == "test_001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_printer_not_found(async_database, event_service):
    """Test connecting non-existent printer raises NotFoundError."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService
    from src.utils.errors import NotFoundError

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await conn_service.connect_printer("nonexistent")

    assert "Printer" in str(exc_info.value)
    assert "nonexistent" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_printer_connection_fails(async_database, event_service):
    """Test printer connection failure."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService
    from src.utils.errors import PrinterConnectionError

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer that fails to connect
    mock_printer = AsyncMock()
    mock_printer.name = "Test Printer"
    mock_printer.connect = AsyncMock(side_effect=Exception("Network timeout"))
    conn_service.printer_instances["test_001"] = mock_printer

    event_service.emit_event = AsyncMock()

    # Act & Assert
    with pytest.raises(PrinterConnectionError) as exc_info:
        await conn_service.connect_printer("test_001")

    assert "test_001" in str(exc_info.value)
    assert "Network timeout" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_printer_success(async_database, event_service):
    """Test successful printer disconnection."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer instance
    mock_printer = AsyncMock()
    mock_printer.name = "Test Printer"
    mock_printer.disconnect = AsyncMock()
    conn_service.printer_instances["test_001"] = mock_printer

    # Track events
    events_emitted = []
    async def capture_event(event_type, data):
        events_emitted.append({"type": event_type, "data": data})
    event_service.emit_event = capture_event

    # Act
    result = await conn_service.disconnect_printer("test_001")

    # Assert
    assert result is True
    mock_printer.disconnect.assert_called_once()

    # Verify event emitted
    assert len(events_emitted) == 1
    assert events_emitted[0]["type"] == "printer_disconnected"
    assert events_emitted[0]["data"]["printer_id"] == "test_001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_disconnect_printer_not_found(async_database, event_service):
    """Test disconnecting non-existent printer raises NotFoundError."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService
    from src.utils.errors import NotFoundError

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Act & Assert
    with pytest.raises(NotFoundError):
        await conn_service.disconnect_printer("nonexistent")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check(async_database, event_service):
    """Test health check returns correct status."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printers
    mock_printer_1 = AsyncMock()
    mock_printer_1.name = "Printer 1"
    mock_printer_1.ip_address = "192.168.1.100"
    mock_printer_1.is_connected = True
    mock_printer_1.health_check = AsyncMock(return_value=True)
    mock_printer_1.last_status = MagicMock()
    mock_printer_1.last_status.timestamp = datetime.now()

    mock_printer_2 = AsyncMock()
    mock_printer_2.name = "Printer 2"
    mock_printer_2.ip_address = "192.168.1.101"
    mock_printer_2.is_connected = False
    mock_printer_2.health_check = AsyncMock(return_value=False)
    mock_printer_2.last_status = None

    conn_service.printer_instances = {
        "printer_001": mock_printer_1,
        "printer_002": mock_printer_2
    }

    # Act
    health = await conn_service.health_check()

    # Assert
    assert health["service_active"] is True
    assert health["total_printers"] == 2
    assert health["connected_printers"] == 1
    assert health["healthy_printers"] == 1
    assert "printer_001" in health["printers"]
    assert health["printers"]["printer_001"]["connected"] is True
    assert health["printers"]["printer_001"]["healthy"] is True
    assert "printer_002" in health["printers"]
    assert health["printers"]["printer_002"]["connected"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shutdown(async_database, event_service):
    """Test graceful shutdown disconnects all printers."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printers
    mock_printer_1 = AsyncMock()
    mock_printer_1.disconnect = AsyncMock()
    mock_printer_2 = AsyncMock()
    mock_printer_2.disconnect = AsyncMock()

    conn_service.printer_instances = {
        "printer_001": mock_printer_1,
        "printer_002": mock_printer_2
    }

    # Act
    await conn_service.shutdown()

    # Assert
    mock_printer_1.disconnect.assert_called_once()
    mock_printer_2.disconnect.assert_called_once()
    assert len(conn_service.printer_instances) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shutdown_handles_errors(async_database, event_service):
    """Test shutdown handles disconnect errors gracefully."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer that fails to disconnect
    mock_printer = AsyncMock()
    mock_printer.disconnect = AsyncMock(side_effect=Exception("Disconnect error"))
    conn_service.printer_instances = {"printer_001": mock_printer}

    # Act - should not raise exception
    await conn_service.shutdown()

    # Assert - instances cleared despite error
    assert len(conn_service.printer_instances) == 0


@pytest.mark.unit
def test_get_printer_instance(async_database, event_service):
    """Test getting printer instance by ID."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer
    mock_printer = MagicMock()
    conn_service.printer_instances["test_001"] = mock_printer

    # Act
    instance = conn_service.get_printer_instance("test_001")
    not_found = conn_service.get_printer_instance("nonexistent")

    # Assert
    assert instance == mock_printer
    assert not_found is None


@pytest.mark.unit
def test_set_file_service(async_database, event_service):
    """Test setting file service updates all printer instances."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printers
    mock_printer_1 = MagicMock()
    mock_printer_2 = MagicMock()
    conn_service.printer_instances = {
        "printer_001": mock_printer_1,
        "printer_002": mock_printer_2
    }

    # Create mock file service
    mock_file_service = MagicMock()

    # Act
    conn_service.set_file_service(mock_file_service)

    # Assert
    assert conn_service.file_service == mock_file_service
    assert mock_printer_1.file_service == mock_file_service
    assert mock_printer_2.file_service == mock_file_service


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_and_monitor_printer_success(async_database, event_service):
    """Test connect_and_monitor_printer with successful connection."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer
    mock_printer = AsyncMock()
    mock_printer.is_connected = False
    mock_printer.connect = AsyncMock(return_value=True)

    # Mock database
    async_database.update_printer_status = AsyncMock()

    # Track events
    events_emitted = []
    async def capture_event(event_type, data):
        events_emitted.append({"type": event_type, "data": data})
    event_service.emit_event = capture_event

    # Mock monitoring callback
    monitoring_called = False
    async def mock_monitoring_callback(pid, instance):
        nonlocal monitoring_called
        monitoring_called = True

    # Act
    await conn_service.connect_and_monitor_printer(
        "test_001",
        mock_printer,
        mock_monitoring_callback
    )

    # Assert
    mock_printer.connect.assert_called_once()
    assert monitoring_called is True

    # Verify events emitted
    event_types = [e["type"] for e in events_emitted]
    assert "printer_connection_progress" in event_types

    # Check for connecting, connected, and monitoring events
    statuses = [e["data"]["status"] for e in events_emitted]
    assert "connecting" in statuses
    assert "connected" in statuses
    assert "monitoring" in statuses


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_and_monitor_printer_already_connected(async_database, event_service):
    """Test connect_and_monitor_printer when already connected."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer that is already connected
    mock_printer = AsyncMock()
    mock_printer.is_connected = True  # Already connected
    mock_printer.connect = AsyncMock()

    event_service.emit_event = AsyncMock()

    # Act
    await conn_service.connect_and_monitor_printer(
        "test_001",
        mock_printer,
        None
    )

    # Assert - should not call connect
    mock_printer.connect.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_and_monitor_printer_connection_fails(async_database, event_service):
    """Test connect_and_monitor_printer when connection fails."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer that fails to connect
    mock_printer = AsyncMock()
    mock_printer.is_connected = False
    mock_printer.connect = AsyncMock(return_value=False)  # Connection fails

    # Track events
    events_emitted = []
    async def capture_event(event_type, data):
        events_emitted.append({"type": event_type, "data": data})
    event_service.emit_event = capture_event

    # Mock monitoring callback
    monitoring_called = False
    async def mock_monitoring_callback(pid, instance):
        nonlocal monitoring_called
        monitoring_called = True

    # Act
    await conn_service.connect_and_monitor_printer(
        "test_001",
        mock_printer,
        mock_monitoring_callback
    )

    # Assert
    mock_printer.connect.assert_called_once()
    assert monitoring_called is False  # Should not start monitoring

    # Verify failure event emitted
    statuses = [e["data"]["status"] for e in events_emitted if e["type"] == "printer_connection_progress"]
    assert "failed" in statuses


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_and_monitor_printer_exception(async_database, event_service):
    """Test connect_and_monitor_printer handles exceptions."""
    # Arrange
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

    from services.printer_connection_service import PrinterConnectionService

    # Mock config service
    mock_config_service = MagicMock()
    mock_config_service.get_active_printers = MagicMock(return_value={})

    conn_service = PrinterConnectionService(
        async_database,
        event_service,
        mock_config_service
    )

    # Create mock printer that raises exception
    mock_printer = AsyncMock()
    mock_printer.is_connected = False
    mock_printer.connect = AsyncMock(side_effect=Exception("Connection error"))

    # Track events
    events_emitted = []
    async def capture_event(event_type, data):
        events_emitted.append({"type": event_type, "data": data})
    event_service.emit_event = capture_event

    # Act - should not raise exception
    await conn_service.connect_and_monitor_printer(
        "test_001",
        mock_printer,
        None
    )

    # Assert - verify error event emitted
    statuses = [e["data"]["status"] for e in events_emitted if e["type"] == "printer_connection_progress"]
    assert "error" in statuses
