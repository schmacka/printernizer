import asyncio
import inspect
import pytest

from src.printers.base import PrinterInterface
from src.printers.prusa import PrusaPrinter
from src.printers.bambu_lab import BambuLabPrinter, BAMBU_AVAILABLE

# NOTE: BambuLabPrinter requires external dependency; we conditionally include it.

REQUIRED_ASYNC_METHODS = [
    'connect', 'disconnect', 'get_status', 'get_job_info', 'list_files',
    'download_file', 'pause_print', 'resume_print', 'stop_print',
    'has_camera', 'get_camera_stream_url', 'take_snapshot'
]

@pytest.mark.asyncio
async def test_printer_interface_methods_signature():
    """Ensure PrinterInterface declares all required abstract async methods."""
    for name in REQUIRED_ASYNC_METHODS:
        assert hasattr(PrinterInterface, name), f"PrinterInterface missing method: {name}"
        attr = getattr(PrinterInterface, name)
        # Abstract coroutine methods appear as function objects decorated by abstractmethod
        assert inspect.isfunction(attr), f"{name} should be a function on PrinterInterface"

@pytest.mark.asyncio
async def test_prusa_printer_implements_interface(monkeypatch):
    """PrusaPrinter must implement all interface methods and maintain async nature."""
    printer = PrusaPrinter(printer_id="test", name="Test Prusa", ip_address="127.0.0.1", api_key="dummy")
    for name in REQUIRED_ASYNC_METHODS:
        assert hasattr(printer, name), f"PrusaPrinter missing method: {name}"
        method = getattr(printer, name)
        assert inspect.iscoroutinefunction(method), f"{name} must be async"

@pytest.mark.asyncio
async def test_bambu_printer_implements_interface(monkeypatch):
    if not BAMBU_AVAILABLE:
        pytest.skip("bambulabs-api not installed; skipping BambuLabPrinter conformance test")
    printer = BambuLabPrinter(printer_id="bambu", name="Bambu", ip_address="127.0.0.1", access_code="x", serial_number="y")
    for name in REQUIRED_ASYNC_METHODS:
        assert hasattr(printer, name), f"BambuLabPrinter missing method: {name}"
        method = getattr(printer, name)
        assert inspect.iscoroutinefunction(method), f"{name} must be async"

