"""
Comprehensive tests for UsageStatisticsRepository.

Tests cover event recording, querying, settings management, and data cleanup.
"""
import pytest
import aiosqlite
from datetime import datetime, timedelta
import json
import uuid

from src.database.repositories.usage_statistics_repository import UsageStatisticsRepository
from src.models.usage_statistics import UsageEvent, EventType


@pytest.fixture
async def async_db_connection(temp_database):
    """Async database connection fixture for repository tests"""
    conn = await aiosqlite.connect(temp_database)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    await conn.close()


@pytest.fixture
async def usage_repo(async_db_connection):
    """Create UsageStatisticsRepository instance for testing"""
    return UsageStatisticsRepository(async_db_connection)


# =====================================================
# Event Insertion Tests
# =====================================================

class TestEventInsertion:
    """Tests for inserting usage events"""

    @pytest.mark.asyncio
    async def test_insert_event_basic(self, usage_repo):
        """Test inserting a basic usage event"""
        event = UsageEvent(
            event_type=EventType.APP_START,
            metadata={"app_version": "2.7.0", "platform": "linux"}
        )

        result = await usage_repo.insert_event(event)

        assert result is True

    @pytest.mark.asyncio
    async def test_insert_event_with_metadata(self, usage_repo):
        """Test inserting event with complex metadata"""
        event = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            metadata={
                "printer_type": "bambu_lab",
                "duration_seconds": 3600,
                "material_used_grams": 25.5,
                "success": True
            }
        )

        result = await usage_repo.insert_event(event)
        assert result is True

        # Verify event can be retrieved
        events = await usage_repo.get_events(event_type=EventType.JOB_COMPLETED.value)
        assert len(events) > 0
        assert events[0]['metadata']['printer_type'] == "bambu_lab"

    @pytest.mark.asyncio
    async def test_insert_event_without_metadata(self, usage_repo):
        """Test inserting event with no metadata"""
        event = UsageEvent(
            event_type=EventType.APP_SHUTDOWN,
            metadata=None
        )

        result = await usage_repo.insert_event(event)

        assert result is True

    @pytest.mark.asyncio
    async def test_insert_event_preserves_id(self, usage_repo):
        """Test that event ID is preserved during insertion"""
        event_id = str(uuid.uuid4())
        event = UsageEvent(
            id=event_id,
            event_type=EventType.PRINTER_CONNECTED,
            metadata={"printer_type": "prusa"}
        )

        await usage_repo.insert_event(event)

        # Retrieve and verify ID
        events = await usage_repo.get_events(event_type=EventType.PRINTER_CONNECTED.value)
        assert any(e['id'] == event_id for e in events)

    @pytest.mark.asyncio
    async def test_insert_multiple_events(self, usage_repo):
        """Test inserting multiple events"""
        events = [
            UsageEvent(event_type=EventType.FILE_DOWNLOADED, metadata={"size": 1000}),
            UsageEvent(event_type=EventType.FILE_UPLOADED, metadata={"size": 2000}),
            UsageEvent(event_type=EventType.JOB_CREATED, metadata={"printer_type": "bambu_lab"}),
        ]

        for event in events:
            result = await usage_repo.insert_event(event)
            assert result is True

        # Verify all were inserted
        total = await usage_repo.get_total_event_count()
        assert total >= 3


# =====================================================
# Event Retrieval Tests
# =====================================================

class TestEventRetrieval:
    """Tests for querying usage events"""

    @pytest.mark.asyncio
    async def test_get_events_all(self, usage_repo):
        """Test retrieving all events"""
        # Insert test events
        for i in range(5):
            event = UsageEvent(
                event_type=EventType.JOB_COMPLETED,
                metadata={"job_number": i}
            )
            await usage_repo.insert_event(event)

        events = await usage_repo.get_events()

        assert len(events) >= 5

    @pytest.mark.asyncio
    async def test_get_events_by_type(self, usage_repo):
        """Test filtering events by type"""
        # Insert mixed events
        await usage_repo.insert_event(UsageEvent(event_type=EventType.APP_START))
        await usage_repo.insert_event(UsageEvent(event_type=EventType.JOB_COMPLETED))
        await usage_repo.insert_event(UsageEvent(event_type=EventType.JOB_COMPLETED))
        await usage_repo.insert_event(UsageEvent(event_type=EventType.APP_SHUTDOWN))

        # Filter by type
        job_events = await usage_repo.get_events(event_type=EventType.JOB_COMPLETED.value)

        assert len(job_events) >= 2
        assert all(e['event_type'] == EventType.JOB_COMPLETED.value for e in job_events)

    @pytest.mark.asyncio
    async def test_get_events_by_date_range(self, usage_repo):
        """Test filtering events by date range"""
        now = datetime.utcnow()
        start_date = now - timedelta(days=7)
        end_date = now

        # Insert event within range
        event = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            timestamp=now - timedelta(days=3)
        )
        await usage_repo.insert_event(event)

        # Query with date range
        events = await usage_repo.get_events(start_date=start_date, end_date=end_date)

        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_get_events_by_submitted_status(self, usage_repo):
        """Test filtering events by submission status"""
        # Insert unsubmitted event
        event = UsageEvent(
            event_type=EventType.FILE_DOWNLOADED,
            submitted=False
        )
        await usage_repo.insert_event(event)

        # Query unsubmitted events
        unsubmitted = await usage_repo.get_events(submitted=False)

        assert len(unsubmitted) > 0
        assert all(not e['submitted'] for e in unsubmitted)

    @pytest.mark.asyncio
    async def test_get_events_with_limit(self, usage_repo):
        """Test limiting number of returned events"""
        # Insert 10 events
        for i in range(10):
            event = UsageEvent(event_type=EventType.JOB_COMPLETED)
            await usage_repo.insert_event(event)

        # Get with limit
        events = await usage_repo.get_events(limit=5)

        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_events_ordered_by_timestamp(self, usage_repo):
        """Test that events are returned in descending timestamp order"""
        # Insert events with different timestamps
        old_event = UsageEvent(
            event_type=EventType.APP_START,
            timestamp=datetime.utcnow() - timedelta(hours=2)
        )
        new_event = UsageEvent(
            event_type=EventType.APP_START,
            timestamp=datetime.utcnow()
        )

        await usage_repo.insert_event(old_event)
        await usage_repo.insert_event(new_event)

        events = await usage_repo.get_events(event_type=EventType.APP_START.value)

        # Most recent should be first
        assert len(events) >= 2
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in events]
        # Verify descending order (most recent first)
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]


# =====================================================
# Event Count Tests
# =====================================================

class TestEventCounts:
    """Tests for event counting and aggregation"""

    @pytest.mark.asyncio
    async def test_get_event_counts_by_type(self, usage_repo):
        """Test getting event counts grouped by type"""
        # Insert various events
        await usage_repo.insert_event(UsageEvent(event_type=EventType.JOB_COMPLETED))
        await usage_repo.insert_event(UsageEvent(event_type=EventType.JOB_COMPLETED))
        await usage_repo.insert_event(UsageEvent(event_type=EventType.FILE_DOWNLOADED))
        await usage_repo.insert_event(UsageEvent(event_type=EventType.ERROR_OCCURRED))

        counts = await usage_repo.get_event_counts_by_type()

        assert counts.get(EventType.JOB_COMPLETED.value, 0) >= 2
        assert counts.get(EventType.FILE_DOWNLOADED.value, 0) >= 1
        assert counts.get(EventType.ERROR_OCCURRED.value, 0) >= 1

    @pytest.mark.asyncio
    async def test_get_event_counts_by_type_with_date_range(self, usage_repo):
        """Test counting events within a date range"""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        # Insert event within range
        event = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            timestamp=now - timedelta(days=3)
        )
        await usage_repo.insert_event(event)

        counts = await usage_repo.get_event_counts_by_type(
            start_date=week_ago,
            end_date=now
        )

        assert counts.get(EventType.JOB_COMPLETED.value, 0) >= 1

    @pytest.mark.asyncio
    async def test_get_total_event_count(self, usage_repo):
        """Test getting total event count"""
        initial_count = await usage_repo.get_total_event_count()

        # Insert 3 events
        for _ in range(3):
            await usage_repo.insert_event(UsageEvent(event_type=EventType.APP_START))

        final_count = await usage_repo.get_total_event_count()

        assert final_count == initial_count + 3

    @pytest.mark.asyncio
    async def test_get_first_event_timestamp(self, usage_repo):
        """Test getting timestamp of first recorded event"""
        # Insert event with known timestamp
        first_timestamp = datetime.utcnow() - timedelta(days=30)
        event = UsageEvent(
            event_type=EventType.APP_START,
            timestamp=first_timestamp
        )
        await usage_repo.insert_event(event)

        result = await usage_repo.get_first_event_timestamp()

        assert result is not None
        assert result <= datetime.utcnow()


# =====================================================
# Event Submission Tests
# =====================================================

class TestEventSubmission:
    """Tests for marking events as submitted"""

    @pytest.mark.asyncio
    async def test_mark_events_submitted(self, usage_repo):
        """Test marking events as submitted"""
        now = datetime.utcnow()
        start = now - timedelta(days=7)

        # Insert unsubmitted event
        event = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            timestamp=now - timedelta(days=3),
            submitted=False
        )
        await usage_repo.insert_event(event)

        # Mark as submitted
        result = await usage_repo.mark_events_submitted(start, now)

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_events_submitted_only_affects_range(self, usage_repo):
        """Test that mark_events_submitted only affects specified date range"""
        now = datetime.utcnow()

        # Insert event inside range
        in_range = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            timestamp=now - timedelta(days=3),
            submitted=False
        )
        await usage_repo.insert_event(in_range)

        # Insert event outside range
        out_of_range = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            timestamp=now - timedelta(days=10),
            submitted=False
        )
        await usage_repo.insert_event(out_of_range)

        # Mark events in last week
        start = now - timedelta(days=7)
        await usage_repo.mark_events_submitted(start, now)

        # Verify unsubmitted events still exist (the out-of-range one)
        unsubmitted = await usage_repo.get_events(submitted=False)
        assert len(unsubmitted) > 0


# =====================================================
# Settings Management Tests
# =====================================================

class TestSettingsManagement:
    """Tests for usage statistics settings"""

    @pytest.mark.asyncio
    async def test_set_and_get_setting(self, usage_repo):
        """Test setting and retrieving a setting"""
        await usage_repo.set_setting("test_key", "test_value")

        value = await usage_repo.get_setting("test_key")

        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_set_setting_overwrites_existing(self, usage_repo):
        """Test that setting a value overwrites existing value"""
        await usage_repo.set_setting("opt_in_status", "disabled")
        await usage_repo.set_setting("opt_in_status", "enabled")

        value = await usage_repo.get_setting("opt_in_status")

        assert value == "enabled"

    @pytest.mark.asyncio
    async def test_get_nonexistent_setting_returns_none(self, usage_repo):
        """Test getting non-existent setting returns None"""
        value = await usage_repo.get_setting("nonexistent_key")

        assert value is None

    @pytest.mark.asyncio
    async def test_get_all_settings(self, usage_repo):
        """Test retrieving all settings"""
        # Set multiple settings
        await usage_repo.set_setting("opt_in_status", "enabled")
        await usage_repo.set_setting("installation_id", str(uuid.uuid4()))
        await usage_repo.set_setting("first_run_date", datetime.utcnow().isoformat())

        settings = await usage_repo.get_all_settings()

        assert "opt_in_status" in settings
        assert "installation_id" in settings
        assert "first_run_date" in settings
        assert settings["opt_in_status"] == "enabled"

    @pytest.mark.asyncio
    async def test_setting_values_stored_as_strings(self, usage_repo):
        """Test that all setting values are stored as strings"""
        await usage_repo.set_setting("numeric_value", "123")
        await usage_repo.set_setting("boolean_value", "true")

        numeric = await usage_repo.get_setting("numeric_value")
        boolean = await usage_repo.get_setting("boolean_value")

        assert isinstance(numeric, str)
        assert isinstance(boolean, str)
        assert numeric == "123"
        assert boolean == "true"


# =====================================================
# Data Deletion Tests
# =====================================================

class TestDataDeletion:
    """Tests for deleting usage statistics data"""

    @pytest.mark.asyncio
    async def test_delete_all_events(self, usage_repo):
        """Test deleting all events"""
        # Insert some events
        for _ in range(5):
            await usage_repo.insert_event(UsageEvent(event_type=EventType.JOB_COMPLETED))

        initial_count = await usage_repo.get_total_event_count()
        assert initial_count >= 5

        # Delete all events
        result = await usage_repo.delete_all_events()

        assert result is True

        # Verify all events are gone
        final_count = await usage_repo.get_total_event_count()
        assert final_count == 0

    @pytest.mark.asyncio
    async def test_delete_all_events_preserves_settings(self, usage_repo):
        """Test that deleting events preserves settings"""
        # Set some settings
        await usage_repo.set_setting("opt_in_status", "enabled")
        await usage_repo.set_setting("installation_id", str(uuid.uuid4()))

        # Insert and delete events
        await usage_repo.insert_event(UsageEvent(event_type=EventType.APP_START))
        await usage_repo.delete_all_events()

        # Verify settings still exist
        opt_in = await usage_repo.get_setting("opt_in_status")
        install_id = await usage_repo.get_setting("installation_id")

        assert opt_in == "enabled"
        assert install_id is not None

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, usage_repo):
        """Test cleaning up old events"""
        now = datetime.utcnow()

        # Insert old event (100 days ago)
        old_event = UsageEvent(
            event_type=EventType.APP_START,
            timestamp=now - timedelta(days=100)
        )
        await usage_repo.insert_event(old_event)

        # Insert recent event (1 day ago)
        recent_event = UsageEvent(
            event_type=EventType.APP_START,
            timestamp=now - timedelta(days=1)
        )
        await usage_repo.insert_event(recent_event)

        # Cleanup events older than 90 days
        deleted_count = await usage_repo.cleanup_old_events(days=90)

        # Should have deleted at least the old event
        assert deleted_count >= 1

        # Recent event should still exist
        events = await usage_repo.get_events(
            start_date=now - timedelta(days=7)
        )
        assert len(events) >= 1


# =====================================================
# Edge Cases and Error Handling Tests
# =====================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_insert_event_with_empty_metadata(self, usage_repo):
        """Test inserting event with empty dict as metadata"""
        event = UsageEvent(
            event_type=EventType.APP_START,
            metadata={}
        )

        result = await usage_repo.insert_event(event)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_events_with_no_matches(self, usage_repo):
        """Test querying events with filters that match nothing"""
        events = await usage_repo.get_events(
            event_type="nonexistent_event_type",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() - timedelta(hours=23)
        )

        assert events == []

    @pytest.mark.asyncio
    async def test_metadata_json_serialization(self, usage_repo):
        """Test that complex metadata is properly JSON serialized"""
        complex_metadata = {
            "nested": {
                "key": "value",
                "number": 42,
                "boolean": True,
                "list": [1, 2, 3]
            },
            "string": "test",
            "null": None
        }

        event = UsageEvent(
            event_type=EventType.JOB_COMPLETED,
            metadata=complex_metadata
        )
        await usage_repo.insert_event(event)

        # Retrieve and verify
        events = await usage_repo.get_events(event_type=EventType.JOB_COMPLETED.value, limit=1)
        assert len(events) > 0
        retrieved_metadata = events[0]['metadata']

        assert retrieved_metadata['nested']['key'] == "value"
        assert retrieved_metadata['nested']['number'] == 42
        assert retrieved_metadata['nested']['boolean'] is True
        assert retrieved_metadata['nested']['list'] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_concurrent_event_insertion(self, usage_repo):
        """Test inserting multiple events concurrently"""
        import asyncio

        # Create multiple events to insert concurrently
        events = [
            UsageEvent(event_type=EventType.JOB_COMPLETED, metadata={"job_id": i})
            for i in range(10)
        ]

        # Insert all concurrently
        results = await asyncio.gather(*[
            usage_repo.insert_event(event) for event in events
        ])

        # All should succeed
        assert all(results)

        # Verify all were inserted
        total = await usage_repo.get_total_event_count()
        assert total >= 10
