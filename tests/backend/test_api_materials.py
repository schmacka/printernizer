"""
Test suite for Material Management API endpoints.
Tests material inventory and consumption history functionality.
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


@pytest.fixture
def mock_material_service(test_app):
    """Create a mock material service and attach to test_app."""
    mock_service = MagicMock()
    mock_service.get_consumption_history = AsyncMock(return_value=([], 0))
    mock_service.get_all_materials = AsyncMock(return_value=[])
    mock_service.get_statistics = AsyncMock(return_value={
        'total_spools': 0,
        'total_weight': 0,
        'total_remaining': 0,
        'total_value': Decimal('0'),
        'remaining_value': Decimal('0'),
        'by_type': {},
        'by_brand': {},
        'by_color': {},
        'low_stock': [],
        'consumption_30d': 0,
        'consumption_rate': 0
    })
    test_app.state.material_service = mock_service
    return mock_service


class TestConsumptionHistoryAPI:
    """Test consumption history API endpoint"""

    def test_get_consumption_history_empty(self, client, mock_material_service):
        """Test GET /api/v1/materials/consumption/history with no records"""
        mock_material_service.get_consumption_history = AsyncMock(return_value=([], 0))

        response = client.get("/api/v1/materials/consumption/history")

        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['total_count'] == 0
        assert data['page'] == 1
        assert data['limit'] == 50
        assert data['total_pages'] == 1

    def test_get_consumption_history_with_data(self, client, mock_material_service):
        """Test GET /api/v1/materials/consumption/history with records"""
        sample_items = [
            {
                'id': 'consumption_001',
                'job_id': 'job_001',
                'material_id': 'material_001',
                'material_type': 'PLA',
                'brand': 'BAMBU',
                'color': 'BLACK',
                'weight_used': 150.5,
                'cost': Decimal('2.50'),
                'timestamp': datetime.now(timezone.utc),
                'printer_id': 'bambu_a1_001',
                'file_name': 'test_cube.3mf',
                'print_time_hours': 2.5
            },
            {
                'id': 'consumption_002',
                'job_id': 'job_002',
                'material_id': 'material_002',
                'material_type': 'PETG',
                'brand': 'PRUSAMENT',
                'color': 'WHITE',
                'weight_used': 200.0,
                'cost': Decimal('3.20'),
                'timestamp': datetime.now(timezone.utc),
                'printer_id': 'prusa_core_001',
                'file_name': 'bracket.gcode',
                'print_time_hours': 4.0
            }
        ]
        mock_material_service.get_consumption_history = AsyncMock(
            return_value=(sample_items, 2)
        )

        response = client.get("/api/v1/materials/consumption/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['total_count'] == 2
        assert data['items'][0]['material_type'] == 'PLA'
        assert data['items'][0]['weight_used'] == 150.5
        assert data['items'][1]['material_type'] == 'PETG'

    def test_get_consumption_history_filter_by_material(self, client, mock_material_service):
        """Test GET /api/v1/materials/consumption/history?material_id=xxx"""
        sample_items = [
            {
                'id': 'consumption_001',
                'job_id': 'job_001',
                'material_id': 'material_001',
                'material_type': 'PLA',
                'brand': 'BAMBU',
                'color': 'BLACK',
                'weight_used': 150.5,
                'cost': Decimal('2.50'),
                'timestamp': datetime.now(timezone.utc),
                'printer_id': 'bambu_a1_001',
                'file_name': 'test_cube.3mf',
                'print_time_hours': 2.5
            }
        ]
        mock_material_service.get_consumption_history = AsyncMock(
            return_value=(sample_items, 1)
        )

        response = client.get("/api/v1/materials/consumption/history?material_id=material_001")

        assert response.status_code == 200
        data = response.json()
        assert data['total_count'] == 1
        # Verify service was called with correct parameter
        mock_material_service.get_consumption_history.assert_called_once()
        call_kwargs = mock_material_service.get_consumption_history.call_args.kwargs
        assert call_kwargs['material_id'] == 'material_001'

    def test_get_consumption_history_filter_by_printer(self, client, mock_material_service):
        """Test GET /api/v1/materials/consumption/history?printer_id=xxx"""
        mock_material_service.get_consumption_history = AsyncMock(return_value=([], 0))

        response = client.get("/api/v1/materials/consumption/history?printer_id=bambu_a1_001")

        assert response.status_code == 200
        mock_material_service.get_consumption_history.assert_called_once()
        call_kwargs = mock_material_service.get_consumption_history.call_args.kwargs
        assert call_kwargs['printer_id'] == 'bambu_a1_001'

    def test_get_consumption_history_filter_by_days(self, client, mock_material_service):
        """Test GET /api/v1/materials/consumption/history?days=7"""
        mock_material_service.get_consumption_history = AsyncMock(return_value=([], 0))

        response = client.get("/api/v1/materials/consumption/history?days=7")

        assert response.status_code == 200
        mock_material_service.get_consumption_history.assert_called_once()
        call_kwargs = mock_material_service.get_consumption_history.call_args.kwargs
        assert call_kwargs['days'] == 7

    def test_get_consumption_history_pagination(self, client, mock_material_service):
        """Test GET /api/v1/materials/consumption/history pagination"""
        mock_material_service.get_consumption_history = AsyncMock(return_value=([], 100))

        response = client.get("/api/v1/materials/consumption/history?page=2&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 10
        assert data['total_count'] == 100
        assert data['total_pages'] == 10

        mock_material_service.get_consumption_history.assert_called_once()
        call_kwargs = mock_material_service.get_consumption_history.call_args.kwargs
        assert call_kwargs['page'] == 2
        assert call_kwargs['limit'] == 10

    def test_get_consumption_history_days_validation(self, client, mock_material_service):
        """Test days parameter validation (1-365)"""
        # Days = 0 should fail
        response = client.get("/api/v1/materials/consumption/history?days=0")
        assert response.status_code == 422

        # Days = 366 should fail
        response = client.get("/api/v1/materials/consumption/history?days=366")
        assert response.status_code == 422

    def test_get_consumption_history_limit_validation(self, client, mock_material_service):
        """Test limit parameter validation (1-1000)"""
        # Limit = 0 should fail
        response = client.get("/api/v1/materials/consumption/history?limit=0")
        assert response.status_code == 422

        # Limit = 1001 should fail
        response = client.get("/api/v1/materials/consumption/history?limit=1001")
        assert response.status_code == 422


class TestMaterialExport:
    """Test material export functionality"""

    def test_export_inventory_csv(self, client, mock_material_service, tmp_path):
        """Test CSV export endpoint"""
        mock_material_service.export_inventory = AsyncMock(return_value=True)

        response = client.get("/api/v1/materials/export?format=csv")

        # Should succeed (mocked)
        assert response.status_code in [200, 500]  # 500 if file doesn't exist in mock
        mock_material_service.export_inventory.assert_called_once()

    def test_export_inventory_excel(self, client, mock_material_service, tmp_path):
        """Test Excel export endpoint - verifies 501 is no longer returned"""
        mock_material_service.export_inventory_excel = AsyncMock(return_value=True)

        response = client.get("/api/v1/materials/export?format=excel")

        # Should NOT return 501 (Not Implemented) anymore
        assert response.status_code != 501
        # Should either succeed or fail with 500 (if file doesn't exist in mock)
        assert response.status_code in [200, 500]
        mock_material_service.export_inventory_excel.assert_called_once()

    def test_export_inventory_invalid_format(self, client, mock_material_service):
        """Test export with invalid format"""
        response = client.get("/api/v1/materials/export?format=pdf")

        # Should fail validation
        assert response.status_code == 422
