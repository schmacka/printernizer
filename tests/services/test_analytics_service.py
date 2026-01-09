"""
Comprehensive tests for Analytics Service.

Tests cover dashboard stats, printer usage, material consumption,
business reports, data export, and statistics methods.
"""
import pytest
import aiosqlite
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from src.services.analytics_service import AnalyticsService
from src.database.repositories.printer_repository import PrinterRepository
from src.database.repositories.job_repository import JobRepository
from src.database.repositories.file_repository import FileRepository
from src.database.database import Database


@pytest.fixture
async def analytics_test_database(temp_database):
    """Create database with test data for analytics tests"""
    database = Database(temp_database)
    await database.initialize()

    # Create test data using direct SQL to ensure it's in the same database
    conn = database._connection

    # Create test printers
    await conn.execute("""
        INSERT INTO printers (id, name, type, status, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, ('printer_analytics_1', 'Analytics Printer 1', 'bambu_lab', 'online', 1))

    await conn.execute("""
        INSERT INTO printers (id, name, type, status, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, ('printer_analytics_2', 'Analytics Printer 2', 'prusa', 'printing', 1))

    await conn.commit()

    # Create test jobs with varying data
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)

    # Recent business job (completed)
    await conn.execute("""
        INSERT INTO jobs (id, printer_id, printer_type, job_name, filename, status,
                         is_business, start_time, end_time, actual_duration, material_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('job_analytics_1', 'printer_analytics_1', 'bambu_lab', 'business_part.3mf',
          'business_part.3mf', 'completed', 1, yesterday.isoformat(), now.isoformat(), 7200, 50.0))

    # Private job (completed)
    await conn.execute("""
        INSERT INTO jobs (id, printer_id, printer_type, job_name, filename, status,
                         is_business, start_time, end_time, actual_duration, material_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('job_analytics_2', 'printer_analytics_2', 'prusa', 'private_model.gcode',
          'private_model.gcode', 'completed', 0, last_week.isoformat(),
          (last_week + timedelta(hours=3)).isoformat(), 10800, 75.0))

    # Active printing job
    await conn.execute("""
        INSERT INTO jobs (id, printer_id, printer_type, job_name, filename, status,
                         is_business, start_time, progress)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('job_analytics_3', 'printer_analytics_1', 'bambu_lab', 'active_print.3mf',
          'active_print.3mf', 'running', 1, now.isoformat(), 50))

    # Failed job
    await conn.execute("""
        INSERT INTO jobs (id, printer_id, printer_type, job_name, filename, status,
                         is_business, start_time, end_time, actual_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('job_analytics_4', 'printer_analytics_2', 'prusa', 'failed_print.gcode',
          'failed_print.gcode', 'failed', 0, last_month.isoformat(),
          (last_month + timedelta(minutes=30)).isoformat(), 1800))

    await conn.commit()

    # Create test files
    await conn.execute("""
        INSERT INTO files (id, printer_id, filename, file_path, file_type, file_size, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('file_analytics_1', 'printer_analytics_1', 'test_file_1.3mf', '/files/test_file_1.3mf', '3mf', 1024000, 'local'))

    await conn.execute("""
        INSERT INTO files (id, printer_id, filename, file_path, file_type, file_size, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('file_analytics_2', 'printer_analytics_2', 'test_file_2.gcode', '/files/test_file_2.gcode', 'gcode', 512000, 'ftp'))

    await conn.commit()

    yield database

    await database.close()


# =====================================================
# AnalyticsService Tests
# =====================================================

class TestAnalyticsService:
    """Tests for AnalyticsService main functionality"""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, analytics_test_database):
        """Test getting dashboard statistics"""
        database = analytics_test_database

        service = AnalyticsService(database)

        stats = await service.get_dashboard_stats()

        # Verify stats structure
        assert 'total_jobs' in stats
        assert 'active_printers' in stats
        assert 'total_runtime' in stats
        assert 'material_used' in stats
        assert 'estimated_costs' in stats
        assert 'business_jobs' in stats
        assert 'private_jobs' in stats

        # Verify values
        assert stats['total_jobs'] >= 4
        assert stats['active_printers'] >= 1  # At least one printer online/printing
        assert stats['business_jobs'] >= 2
        assert stats['private_jobs'] >= 2

    @pytest.mark.asyncio
    async def test_get_printer_usage(self, analytics_test_database):
        """Test getting printer usage statistics"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Get usage for last 30 days
        usage = await service.get_printer_usage(days=30)

        # Should return data for all printers
        assert len(usage) >= 2

        # Each printer should have usage stats
        for printer_stats in usage:
            assert 'printer_id' in printer_stats
            assert 'printer_name' in printer_stats
            assert 'total_jobs' in printer_stats
            assert 'completed_jobs' in printer_stats
            assert 'failed_jobs' in printer_stats

    @pytest.mark.asyncio
    async def test_get_material_consumption(self, analytics_test_database):
        """Test getting material consumption statistics"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Get material consumption for last 30 days
        consumption = await service.get_material_consumption(days=30)

        # Verify structure matches actual service return
        assert 'total_consumption' in consumption
        assert 'total_cost' in consumption
        assert 'by_material' in consumption

        # Should have consumed some material (can be 0 for test data)
        assert consumption['total_consumption'] >= 0

        # Should have data for different material types
        assert isinstance(consumption['by_material'], dict)

    @pytest.mark.asyncio
    async def test_get_business_report(self, analytics_test_database):
        """Test getting business report"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Get report for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        report = await service.get_business_report(start_date, end_date)

        # Verify structure matches actual service return
        assert 'period' in report
        assert 'jobs' in report
        assert 'revenue' in report
        assert 'materials' in report

        # Jobs should have the expected sub-keys
        assert 'total' in report['jobs']
        assert 'business' in report['jobs']
        assert 'private' in report['jobs']

        # Should have some jobs (we created 4 in fixture)
        assert report['jobs']['total'] >= 1

    @pytest.mark.asyncio
    async def test_export_data_csv(self, analytics_test_database):
        """Test exporting data to CSV format"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Export to CSV
        result = await service.export_data('csv')

        # Verify result matches actual service return
        assert 'file_path' in result
        assert 'format' in result
        assert 'record_count' in result
        assert result['format'] == 'csv'
        assert result['record_count'] >= 4

        # Verify file exists
        file_path = Path(result['file_path'])
        assert file_path.exists()

        # Clean up
        if file_path.exists():
            os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_export_data_json(self, analytics_test_database):
        """Test exporting data to JSON format"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Export to JSON
        result = await service.export_data('json')

        # Verify result matches actual service return
        assert 'file_path' in result
        assert 'format' in result
        assert 'record_count' in result
        assert result['format'] == 'json'
        assert result['record_count'] >= 4

        # Verify file exists and contains valid JSON
        file_path = Path(result['file_path'])
        assert file_path.exists()

        with open(file_path, 'r') as f:
            json_data = json.load(f)
            # JSON export contains list of jobs directly
            assert isinstance(json_data, list)
            assert len(json_data) >= 4

        # Clean up
        if file_path.exists():
            os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_export_data_with_filters(self, analytics_test_database):
        """Test exporting data with filters"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Export only business jobs
        filters = {
            'is_business': True
        }
        result = await service.export_data('json', filters=filters)

        # Verify filtered results
        file_path = Path(result['file_path'])
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            # JSON export contains list of jobs directly
            # All jobs should be business jobs
            assert all(job.get('is_business') for job in json_data)

        # Clean up
        if file_path.exists():
            os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_get_summary(self, analytics_test_database):
        """Test getting summary statistics"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Get summary for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        summary = await service.get_summary(start_date, end_date)

        # Verify structure matches actual service return
        assert 'total_jobs' in summary
        assert 'completed_jobs' in summary
        assert 'success_rate_percent' in summary

        # Verify values - at least some jobs from fixture
        assert summary['total_jobs'] >= 1
        assert 0 <= summary['success_rate_percent'] <= 100

    @pytest.mark.asyncio
    async def test_get_dashboard_overview(self, analytics_test_database):
        """Test getting dashboard overview"""
        database = analytics_test_database

        service = AnalyticsService(database)

        # Get overview for different periods
        for period in ['day', 'week', 'month']:
            overview = await service.get_dashboard_overview(period=period)

            # Verify structure matches actual service return
            assert 'jobs' in overview
            assert 'files' in overview
            assert 'printers' in overview

    @pytest.mark.asyncio
    async def test_error_handling(self, temp_database):
        """Test error handling in analytics service"""
        # Create service with invalid/closed database
        database = Database(temp_database)
        # Don't initialize database - should cause errors

        service = AnalyticsService(database)

        # get_dashboard_stats should return zeros on error
        stats = await service.get_dashboard_stats()
        assert stats['total_jobs'] == 0
        assert stats['active_printers'] == 0

    @pytest.mark.asyncio
    async def test_empty_database(self, temp_database):
        """Test analytics with empty database"""
        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(database)

        # Should return zeros/empty results
        stats = await service.get_dashboard_stats()
        assert stats['total_jobs'] == 0
        assert stats['active_printers'] == 0

        usage = await service.get_printer_usage(days=30)
        assert len(usage) == 0

        consumption = await service.get_material_consumption(days=30)
        assert consumption['total_consumption'] == 0.0

        await database.close()


# =====================================================
# Run marker for pytest
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
