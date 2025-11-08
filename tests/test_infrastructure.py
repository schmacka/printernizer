"""
Test to verify Phase 3 test infrastructure is working correctly.
"""
import pytest


@pytest.mark.unit
def test_event_service_fixture(event_service):
    """Test that EventService fixture works."""
    assert event_service is not None
    assert hasattr(event_service, 'subscribe')
    assert hasattr(event_service, 'emit_event')
    assert event_service._running is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_database_fixture(async_database):
    """Test that async Database fixture works."""
    assert async_database is not None
    assert async_database._connection is not None

    # Test basic database operation
    async with async_database._connection.cursor() as cursor:
        await cursor.execute("SELECT 1")
        result = await cursor.fetchone()
        assert result is not None


@pytest.mark.unit
def test_mock_printer_fixture(mock_printer_instance):
    """Test that mock printer fixture works."""
    assert mock_printer_instance is not None
    assert mock_printer_instance.printer_id == "test_printer_001"
    assert mock_printer_instance.name == "Test Printer"
    assert mock_printer_instance.printer_type == "bambu_lab"


@pytest.mark.unit
def test_sample_data_fixtures(sample_printer_data, sample_job_data, sample_file_data):
    """Test that sample data fixtures work."""
    assert len(sample_printer_data) == 2
    assert len(sample_job_data) == 2
    assert len(sample_file_data) == 2

    # Verify data structure
    assert sample_printer_data[0]['type'] == 'bambu_lab'
    assert sample_printer_data[1]['type'] == 'prusa'
    assert sample_job_data[0]['is_business'] is True
    assert sample_file_data[0]['file_type'] == '.3mf'


@pytest.mark.unit
def test_test_utils_fixture(test_utils):
    """Test that test utilities fixture works."""
    assert test_utils is not None

    # Test VAT calculation
    vat = test_utils.calculate_vat(100.0, 0.19)
    assert vat == 19.0

    # Test currency formatting
    formatted = test_utils.format_currency(123.45)
    assert "123.45" in formatted
    assert "EUR" in formatted
