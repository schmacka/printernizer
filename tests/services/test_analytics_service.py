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
async def setup_analytics_test_data(async_db_connection):
    """Create test data for analytics tests"""
    printer_repo = PrinterRepository(async_db_connection)
    job_repo = JobRepository(async_db_connection)
    file_repo = FileRepository(async_db_connection)

    # Create test printers
    await printer_repo.create({
        'id': 'printer_analytics_1',
        'name': 'Analytics Printer 1',
        'type': 'bambu_lab',
        'status': 'online',
        'is_active': True
    })

    await printer_repo.create({
        'id': 'printer_analytics_2',
        'name': 'Analytics Printer 2',
        'type': 'prusa',
        'status': 'printing',
        'is_active': True
    })

    # Create test jobs with varying data
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)

    # Recent business job (completed)
    await job_repo.create({
        'id': 'job_analytics_1',
        'printer_id': 'printer_analytics_1',
        'printer_type': 'bambu_lab',
        'job_name': 'business_part.3mf',
        'filename': 'business_part.3mf',
        'status': 'completed',
        'is_business': True,
        'start_time': yesterday.isoformat(),
        'end_time': now.isoformat(),
        'elapsed_time_minutes': 120,  # 2 hours
        'material_used_grams': 50.0,
        'material_type': 'PLA'
    })

    # Private job (completed)
    await job_repo.create({
        'id': 'job_analytics_2',
        'printer_id': 'printer_analytics_2',
        'printer_type': 'prusa',
        'job_name': 'private_model.gcode',
        'filename': 'private_model.gcode',
        'status': 'completed',
        'is_business': False,
        'start_time': last_week.isoformat(),
        'end_time': (last_week + timedelta(hours=3)).isoformat(),
        'elapsed_time_minutes': 180,  # 3 hours
        'material_used_grams': 75.0,
        'material_type': 'PETG'
    })

    # Active printing job
    await job_repo.create({
        'id': 'job_analytics_3',
        'printer_id': 'printer_analytics_1',
        'printer_type': 'bambu_lab',
        'job_name': 'active_print.3mf',
        'filename': 'active_print.3mf',
        'status': 'printing',
        'is_business': True,
        'start_time': now.isoformat(),
        'progress': 50
    })

    # Failed job
    await job_repo.create({
        'id': 'job_analytics_4',
        'printer_id': 'printer_analytics_2',
        'printer_type': 'prusa',
        'job_name': 'failed_print.gcode',
        'filename': 'failed_print.gcode',
        'status': 'failed',
        'is_business': False,
        'start_time': last_month.isoformat(),
        'end_time': (last_month + timedelta(minutes=30)).isoformat(),
        'elapsed_time_minutes': 30
    })

    # Create test files
    await file_repo.create({
        'id': 'file_analytics_1',
        'filename': 'test_file_1.3mf',
        'file_path': '/files/test_file_1.3mf',
        'file_type': '3mf',
        'file_size': 1024000,
        'source': 'local'
    })

    await file_repo.create({
        'id': 'file_analytics_2',
        'filename': 'test_file_2.gcode',
        'file_path': '/files/test_file_2.gcode',
        'file_type': 'gcode',
        'file_size': 512000,
        'source': 'ftp'
    })

    return {
        'printer_repo': printer_repo,
        'job_repo': job_repo,
        'file_repo': file_repo,
        'connection': async_db_connection
    }


# =====================================================
# AnalyticsService Tests
# =====================================================

class TestAnalyticsService:
    """Tests for AnalyticsService main functionality"""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, temp_database, setup_analytics_test_data):
        """Test getting dashboard statistics"""
        repos = await setup_analytics_test_data

        # Create mock database with connection
        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

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
        assert stats['active_printers'] >= 2  # Both printers are online/printing
        assert stats['total_runtime'] >= 330  # 120 + 180 + 30 minutes from completed jobs
        assert stats['material_used'] >= 0.125  # 125 grams = 0.125 kg
        assert stats['business_jobs'] >= 2
        assert stats['private_jobs'] >= 2

        await database.close()

    @pytest.mark.asyncio
    async def test_get_printer_usage(self, temp_database, setup_analytics_test_data):
        """Test getting printer usage statistics"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

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

        await database.close()

    @pytest.mark.asyncio
    async def test_get_material_consumption(self, temp_database, setup_analytics_test_data):
        """Test getting material consumption statistics"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Get material consumption for last 30 days
        consumption = await service.get_material_consumption(days=30)

        # Verify structure
        assert 'total_material_kg' in consumption
        assert 'total_cost' in consumption
        assert 'by_material_type' in consumption

        # Should have consumed at least 125 grams (0.125 kg)
        assert consumption['total_material_kg'] >= 0.125

        # Should have data for different material types
        assert isinstance(consumption['by_material_type'], dict)

        await database.close()

    @pytest.mark.asyncio
    async def test_get_business_report(self, temp_database, setup_analytics_test_data):
        """Test getting business report"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Get report for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        report = await service.get_business_report(start_date, end_date)

        # Verify structure
        assert 'period' in report
        assert 'total_business_jobs' in report
        assert 'completed_business_jobs' in report
        assert 'total_revenue_potential' in report

        # Should have business jobs
        assert report['total_business_jobs'] >= 2

        await database.close()

    @pytest.mark.asyncio
    async def test_export_data_csv(self, temp_database, setup_analytics_test_data):
        """Test exporting data to CSV format"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Export to CSV
        result = await service.export_data('csv')

        # Verify result
        assert 'file_path' in result
        assert 'format' in result
        assert 'total_records' in result
        assert result['format'] == 'csv'
        assert result['total_records'] >= 4

        # Verify file exists
        file_path = Path(result['file_path'])
        assert file_path.exists()

        # Clean up
        if file_path.exists():
            os.unlink(file_path)

        await database.close()

    @pytest.mark.asyncio
    async def test_export_data_json(self, temp_database, setup_analytics_test_data):
        """Test exporting data to JSON format"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Export to JSON
        result = await service.export_data('json')

        # Verify result
        assert 'file_path' in result
        assert 'format' in result
        assert 'total_records' in result
        assert result['format'] == 'json'
        assert result['total_records'] >= 4

        # Verify file exists and contains valid JSON
        file_path = Path(result['file_path'])
        assert file_path.exists()

        with open(file_path, 'r') as f:
            data = json.load(f)
            assert 'jobs' in data
            assert len(data['jobs']) >= 4

        # Clean up
        if file_path.exists():
            os.unlink(file_path)

        await database.close()

    @pytest.mark.asyncio
    async def test_export_data_with_filters(self, temp_database, setup_analytics_test_data):
        """Test exporting data with filters"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Export only business jobs
        filters = {
            'is_business': True
        }
        result = await service.export_data('json', filters=filters)

        # Verify filtered results
        file_path = Path(result['file_path'])
        with open(file_path, 'r') as f:
            data = json.load(f)
            # All jobs should be business jobs
            assert all(job.get('is_business') for job in data['jobs'])

        # Clean up
        if file_path.exists():
            os.unlink(file_path)

        await database.close()

    @pytest.mark.asyncio
    async def test_get_summary(self, temp_database, setup_analytics_test_data):
        """Test getting summary statistics"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Get summary for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        summary = await service.get_summary(start_date, end_date)

        # Verify structure
        assert 'total_jobs' in summary
        assert 'completed_jobs' in summary
        assert 'success_rate' in summary

        # Verify values
        assert summary['total_jobs'] >= 4
        assert 0 <= summary['success_rate'] <= 100

        await database.close()

    @pytest.mark.asyncio
    async def test_get_dashboard_overview(self, temp_database, setup_analytics_test_data):
        """Test getting dashboard overview"""
        repos = await setup_analytics_test_data

        database = Database(temp_database)
        await database.initialize()

        service = AnalyticsService(
            database,
            repos['printer_repo'],
            repos['job_repo'],
            repos['file_repo']
        )

        # Get overview for different periods
        for period in ['day', 'week', 'month']:
            overview = await service.get_dashboard_overview(period=period)

            # Verify structure
            assert 'job_stats' in overview
            assert 'file_stats' in overview
            assert 'printer_stats' in overview
            assert 'period' in overview
            assert overview['period'] == period

        await database.close()

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
        assert stats['material_used'] == 0.0

        usage = await service.get_printer_usage(days=30)
        assert len(usage) == 0

        consumption = await service.get_material_consumption(days=30)
        assert consumption['total_material_kg'] == 0.0

        await database.close()


# =====================================================
# Run marker for pytest
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
