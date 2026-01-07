"""
Unit tests for SlicerService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from src.services.slicer_service import SlicerService
from src.services.event_service import EventService
from src.models.slicer import SlicerType, ProfileType, SlicerConfig, SlicerProfile
from src.utils.errors import NotFoundError


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    db = MagicMock()
    db.connection = MagicMock()
    
    # Setup async context manager
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.commit = AsyncMock()
    
    async_context = AsyncMock()
    async_context.__aenter__ = AsyncMock(return_value=mock_conn)
    async_context.__aexit__ = AsyncMock()
    
    db.connection.return_value = async_context
    
    return db


@pytest.fixture
def mock_event_service():
    """Create mock event service for testing."""
    event_service = MagicMock(spec=EventService)
    event_service.emit = AsyncMock()
    return event_service


@pytest.fixture
def slicer_service(mock_database, mock_event_service):
    """Create SlicerService instance with mock dependencies."""
    service = SlicerService(mock_database, mock_event_service)
    return service


class TestSlicerService:
    """Test slicer service functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self, slicer_service):
        """Test service initialization."""
        assert slicer_service.db is not None
        assert slicer_service.event_service is not None
        assert slicer_service.detector is not None

    @pytest.mark.asyncio
    async def test_register_slicer(self, slicer_service, mock_database, mock_event_service):
        """Test registering a slicer."""
        slicer_data = {
            'name': 'PrusaSlicer',
            'slicer_type': SlicerType.PRUSASLICER.value,
            'executable_path': '/usr/bin/prusa-slicer',
            'version': '2.7.0',
            'config_dir': '/home/user/.config/PrusaSlicer'
        }
        
        # Mock the get_slicer call that happens after registration
        with patch.object(slicer_service, 'get_slicer') as mock_get:
            mock_get.return_value = SlicerConfig(
                id='test-id',
                name=slicer_data['name'],
                slicer_type=slicer_data['slicer_type'],
                executable_path=slicer_data['executable_path'],
                version=slicer_data['version'],
                config_dir=slicer_data['config_dir'],
                is_available=True,
                last_verified=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            result = await slicer_service.register_slicer(slicer_data)
            
            assert result is not None
            assert result.name == slicer_data['name']
            assert result.slicer_type == slicer_data['slicer_type']

    @pytest.mark.asyncio
    async def test_get_slicer_found(self, slicer_service, mock_database):
        """Test getting a slicer by ID."""
        slicer_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Setup mock database response
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchone.return_value = (
            slicer_id,
            'PrusaSlicer',
            SlicerType.PRUSASLICER.value,
            '/usr/bin/prusa-slicer',
            '2.7.0',
            '/home/user/.config/PrusaSlicer',
            True,
            now.isoformat(),
            now.isoformat(),
            now.isoformat()
        )
        
        result = await slicer_service.get_slicer(slicer_id)
        
        assert result is not None
        assert result.id == slicer_id
        assert result.name == 'PrusaSlicer'
        assert result.slicer_type == SlicerType.PRUSASLICER

    @pytest.mark.asyncio
    async def test_get_slicer_not_found(self, slicer_service, mock_database):
        """Test getting non-existent slicer."""
        slicer_id = str(uuid.uuid4())
        
        # Setup mock to return None
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchone.return_value = None
        
        with pytest.raises(NotFoundError):
            await slicer_service.get_slicer(slicer_id)

    @pytest.mark.asyncio
    async def test_list_slicers(self, slicer_service, mock_database):
        """Test listing all slicers."""
        now = datetime.now()
        
        # Setup mock database response
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchall.return_value = [
            (
                'id1',
                'PrusaSlicer',
                SlicerType.PRUSASLICER.value,
                '/usr/bin/prusa-slicer',
                '2.7.0',
                '/config/prusa',
                True,
                now.isoformat(),
                now.isoformat(),
                now.isoformat()
            ),
            (
                'id2',
                'BambuStudio',
                SlicerType.BAMBUSTUDIO.value,
                '/usr/bin/bambustudio',
                '1.9.0',
                '/config/bambu',
                True,
                now.isoformat(),
                now.isoformat(),
                now.isoformat()
            )
        ]
        
        results = await slicer_service.list_slicers()
        
        assert len(results) == 2
        assert results[0].name == 'PrusaSlicer'
        assert results[1].name == 'BambuStudio'

    @pytest.mark.asyncio
    async def test_list_slicers_available_only(self, slicer_service, mock_database):
        """Test listing only available slicers."""
        now = datetime.now()
        
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchall.return_value = [
            (
                'id1',
                'PrusaSlicer',
                SlicerType.PRUSASLICER.value,
                '/usr/bin/prusa-slicer',
                '2.7.0',
                '/config/prusa',
                True,
                now.isoformat(),
                now.isoformat(),
                now.isoformat()
            )
        ]
        
        results = await slicer_service.list_slicers(available_only=True)
        
        assert len(results) == 1
        assert results[0].is_available is True

    @pytest.mark.asyncio
    async def test_update_slicer(self, slicer_service, mock_database):
        """Test updating slicer configuration."""
        slicer_id = str(uuid.uuid4())
        updates = {
            'name': 'Updated PrusaSlicer',
            'version': '2.8.0'
        }
        
        with patch.object(slicer_service, 'get_slicer') as mock_get:
            now = datetime.now()
            mock_get.return_value = SlicerConfig(
                id=slicer_id,
                name=updates['name'],
                slicer_type=SlicerType.PRUSASLICER,
                executable_path='/usr/bin/prusa-slicer',
                version=updates['version'],
                config_dir='/config',
                is_available=True,
                last_verified=now,
                created_at=now,
                updated_at=now
            )
            
            result = await slicer_service.update_slicer(slicer_id, updates)
            
            assert result.name == updates['name']
            assert result.version == updates['version']

    @pytest.mark.asyncio
    async def test_delete_slicer(self, slicer_service, mock_database):
        """Test deleting slicer configuration."""
        slicer_id = str(uuid.uuid4())
        
        result = await slicer_service.delete_slicer(slicer_id)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_create_profile(self, slicer_service, mock_database):
        """Test creating a slicer profile."""
        slicer_id = str(uuid.uuid4())
        profile_data = {
            'profile_name': '0.2mm SPEED',
            'profile_type': ProfileType.PRINT.value,
            'profile_path': '/config/prusa/print/0.2mm_SPEED.ini'
        }
        
        with patch.object(slicer_service, 'get_profile') as mock_get:
            now = datetime.now()
            mock_get.return_value = SlicerProfile(
                id='profile-id',
                slicer_id=slicer_id,
                profile_name=profile_data['profile_name'],
                profile_type=profile_data['profile_type'],
                profile_path=profile_data['profile_path'],
                settings_json=None,
                compatible_printers=None,
                is_default=False,
                created_at=now,
                updated_at=now
            )
            
            result = await slicer_service.create_profile(slicer_id, profile_data)
            
            assert result is not None
            assert result.profile_name == profile_data['profile_name']
            assert result.profile_type == profile_data['profile_type']

    @pytest.mark.asyncio
    async def test_list_profiles(self, slicer_service, mock_database):
        """Test listing profiles."""
        now = datetime.now()
        
        async_context = mock_database.connection.return_value
        conn = await async_context.__aenter__()
        cursor = await conn.execute()
        cursor.fetchall.return_value = [
            (
                'profile1',
                'slicer1',
                '0.2mm SPEED',
                ProfileType.PRINT.value,
                '/path/to/profile.ini',
                None,
                None,
                False,
                now.isoformat(),
                now.isoformat()
            )
        ]
        
        results = await slicer_service.list_profiles()
        
        assert len(results) == 1
        assert results[0].profile_name == '0.2mm SPEED'

    @pytest.mark.asyncio
    async def test_verify_slicer_availability(self, slicer_service, mock_database):
        """Test verifying slicer availability."""
        slicer_id = str(uuid.uuid4())
        
        with patch.object(slicer_service, 'get_slicer') as mock_get:
            now = datetime.now()
            mock_get.return_value = SlicerConfig(
                id=slicer_id,
                name='PrusaSlicer',
                slicer_type=SlicerType.PRUSASLICER,
                executable_path='/usr/bin/prusa-slicer',
                version='2.7.0',
                config_dir='/config',
                is_available=True,
                last_verified=now,
                created_at=now,
                updated_at=now
            )
            
            with patch.object(slicer_service.detector, 'verify_slicer') as mock_verify:
                mock_verify.return_value = (True, None)
                
                result = await slicer_service.verify_slicer_availability(slicer_id)
                
                assert result is True

    @pytest.mark.asyncio
    async def test_detect_and_register_slicers(self, slicer_service, mock_event_service):
        """Test detecting and registering slicers."""
        detected_data = [
            {
                'name': 'PrusaSlicer',
                'slicer_type': SlicerType.PRUSASLICER.value,
                'executable_path': '/usr/bin/prusa-slicer',
                'version': '2.7.0',
                'config_dir': '/config/prusa'
            }
        ]
        
        with patch.object(slicer_service.detector, 'detect_all') as mock_detect:
            mock_detect.return_value = detected_data
            
            with patch.object(slicer_service, 'register_slicer') as mock_register:
                now = datetime.now()
                mock_register.return_value = SlicerConfig(
                    id='test-id',
                    name='PrusaSlicer',
                    slicer_type=SlicerType.PRUSASLICER,
                    executable_path='/usr/bin/prusa-slicer',
                    version='2.7.0',
                    config_dir='/config/prusa',
                    is_available=True,
                    last_verified=now,
                    created_at=now,
                    updated_at=now
                )
                
                results = await slicer_service.detect_and_register_slicers()
                
                assert len(results) == 1
                assert results[0].name == 'PrusaSlicer'
                mock_event_service.emit.assert_called()
