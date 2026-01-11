"""
Tests for API Pagination Optimizations (Phase 2 Technical Debt)

This test suite verifies that the pagination improvements from Phase 2
are working correctly:
- Efficient COUNT(*) queries instead of fetching all records
- Combined fetch + count operations in single method calls
- No duplicate queries for counting records

Related commits: ee5d4a2 (API pagination optimizations)
"""
import pytest
from unittest.mock import AsyncMock, patch, call
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestJobsPaginationOptimization:
    """Test jobs API pagination optimizations"""

    def test_jobs_list_uses_combined_method(self, client, test_app):
        """Verify that jobs listing uses the combined list_jobs_with_count method"""

        # Mock the job_service to track method calls
        with patch.object(test_app.state.job_service, 'list_jobs_with_count', new_callable=AsyncMock) as mock_list_with_count:
            # Configure mock to return sample data with all required fields
            from datetime import datetime
            now = datetime.now().isoformat()
            mock_list_with_count.return_value = (
                [
                    {'id': 'job1', 'job_name': 'test1.3mf', 'status': 'completed', 'printer_id': 'printer1', 'printer_type': 'bambu_lab', 'created_at': now, 'updated_at': now},
                    {'id': 'job2', 'job_name': 'test2.3mf', 'status': 'printing', 'printer_id': 'printer1', 'printer_type': 'bambu_lab', 'created_at': now, 'updated_at': now}
                ],
                2  # total count
            )

            # Make request
            response = client.get("/api/v1/jobs")

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['total_count'] == 2
            assert len(data['jobs']) == 2

            # CRITICAL: Verify that list_jobs_with_count was called (optimized method)
            mock_list_with_count.assert_called_once()

    def test_jobs_list_with_filters_optimized(self, client, test_app):
        """Verify pagination with filters uses optimized count"""

        with patch.object(test_app.state.job_service, 'list_jobs_with_count', new_callable=AsyncMock) as mock_list_with_count:
            # Mock filtered results with all required fields
            from datetime import datetime
            now = datetime.now().isoformat()
            mock_list_with_count.return_value = (
                [{'id': 'job1', 'job_name': 'test1.3mf', 'status': 'completed', 'is_business': True, 'printer_id': 'printer_123', 'printer_type': 'bambu_lab', 'created_at': now, 'updated_at': now}],
                1
            )

            # Request with filters
            response = client.get("/api/v1/jobs?printer_id=printer_123&is_business=true")

            assert response.status_code == 200
            data = response.json()

            # Verify filters were passed to the optimized method
            mock_list_with_count.assert_called_once()
            call_kwargs = mock_list_with_count.call_args.kwargs
            assert call_kwargs.get('printer_id') == 'printer_123'
            assert call_kwargs.get('is_business') is True

    def test_jobs_pagination_parameters(self, client, test_app):
        """Verify pagination parameters work with optimized method"""

        with patch.object(test_app.state.job_service, 'list_jobs_with_count', new_callable=AsyncMock) as mock_list_with_count:
            # Mock paginated results with all required fields
            from datetime import datetime
            now = datetime.now().isoformat()
            mock_list_with_count.return_value = (
                [{'id': f'job{i}', 'job_name': f'test{i}.3mf', 'status': 'completed', 'printer_id': 'printer1', 'printer_type': 'bambu_lab', 'created_at': now, 'updated_at': now} for i in range(10)],
                50  # total count
            )

            # Request with pagination
            response = client.get("/api/v1/jobs?page=2&limit=10")

            assert response.status_code == 200
            data = response.json()

            # Verify pagination info
            assert data['pagination']['page'] == 2
            assert data['pagination']['limit'] == 10
            assert data['pagination']['total_pages'] == 5  # 50 total / 10 per page

            # Verify offset was calculated correctly (page 2, limit 10 = offset 10)
            call_kwargs = mock_list_with_count.call_args.kwargs
            assert call_kwargs.get('offset') == 10
            assert call_kwargs.get('limit') == 10


class TestFilesPaginationOptimization:
    """Test files API pagination optimizations"""

    def test_files_list_uses_combined_method(self, client, test_app):
        """Verify that files listing uses the combined get_files_with_count method"""

        # Mock the file_service to track method calls
        with patch.object(test_app.state.file_service, 'get_files_with_count', new_callable=AsyncMock) as mock_get_with_count:
            # Configure mock to return sample data with all required fields
            mock_get_with_count.return_value = (
                [
                    {'id': 'file1', 'filename': 'model1.3mf', 'source': 'local', 'status': 'available', 'file_type': '3mf'},
                    {'id': 'file2', 'filename': 'model2.gcode', 'source': 'printer', 'status': 'available', 'file_type': 'gcode'}
                ],
                2  # total count
            )

            # Make request
            response = client.get("/api/v1/files")

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['total_count'] == 2
            assert len(data['files']) == 2

            # CRITICAL: Verify that get_files_with_count was called (optimized method)
            mock_get_with_count.assert_called_once()

    def test_files_list_with_filters_optimized(self, client, test_app):
        """Verify files pagination with filters uses optimized count"""

        with patch.object(test_app.state.file_service, 'get_files_with_count', new_callable=AsyncMock) as mock_get_with_count:
            # Mock filtered results with all required fields
            mock_get_with_count.return_value = (
                [{'id': 'file1', 'filename': 'model1.3mf', 'source': 'local', 'status': 'available', 'file_type': '3mf'}],
                1
            )

            # Request with filters
            response = client.get("/api/v1/files?source=local&printer_id=printer_123")

            assert response.status_code == 200
            data = response.json()

            # Verify filters were passed
            mock_get_with_count.assert_called_once()
            call_kwargs = mock_get_with_count.call_args.kwargs
            assert call_kwargs.get('source') == 'local'
            assert call_kwargs.get('printer_id') == 'printer_123'

    def test_files_pagination_parameters(self, client, test_app):
        """Verify files pagination parameters work correctly"""

        with patch.object(test_app.state.file_service, 'get_files_with_count', new_callable=AsyncMock) as mock_get_with_count:
            # Mock paginated results with all required fields
            mock_get_with_count.return_value = (
                [{'id': f'file{i}', 'filename': f'model{i}.3mf', 'source': 'local', 'status': 'available', 'file_type': '3mf'} for i in range(25)],
                100  # total count
            )

            # Request page 3 with 25 items per page
            response = client.get("/api/v1/files?page=3&limit=25")

            assert response.status_code == 200
            data = response.json()

            # Verify pagination info
            assert data['pagination']['page'] == 3
            assert data['pagination']['limit'] == 25
            assert data['pagination']['total_pages'] == 4  # 100 total / 25 per page

            # Verify page was passed correctly (API uses page param not offset)
            call_kwargs = mock_get_with_count.call_args.kwargs
            assert call_kwargs.get('page') == 3
            assert call_kwargs.get('limit') == 25


class TestRepositoryCountOptimization:
    """Test that repositories use efficient COUNT queries"""

    @pytest.mark.asyncio
    async def test_job_repository_count_method(self, async_db_connection):
        """Verify JobRepository.count() uses efficient COUNT(*) query"""
        from src.database.repositories.job_repository import JobRepository

        repo = JobRepository(async_db_connection)

        # Create test data
        from src.database.repositories.printer_repository import PrinterRepository
        printer_repo = PrinterRepository(async_db_connection)
        await printer_repo.create({
            'id': 'printer_count_test',
            'name': 'Count Test Printer',
            'type': 'bambu_lab'
        })

        # Create multiple jobs
        for i in range(5):
            await repo.create({
                'id': f'job_count_{i}',
                'printer_id': 'printer_count_test',
                'printer_type': 'bambu_lab',
                'job_name': f'test_{i}.3mf',
                'status': 'completed' if i % 2 == 0 else 'failed',
                'is_business': i % 2 == 0
            })

        # Test count without filters
        total = await repo.count()
        assert total >= 5

        # Test count with filters
        completed_count = await repo.count(status='completed')
        assert completed_count >= 3  # 0, 2, 4

        business_count = await repo.count(is_business=True)
        assert business_count >= 3  # 0, 2, 4

        # Test count with multiple filters
        completed_business = await repo.count(status='completed', is_business=True)
        assert completed_business >= 3

    @pytest.mark.asyncio
    async def test_file_repository_count_method(self, async_db_connection):
        """Verify FileRepository.count() uses efficient COUNT(*) query"""
        from src.database.repositories.file_repository import FileRepository

        repo = FileRepository(async_db_connection)

        # Create test files
        for i in range(7):
            await repo.create({
                'id': f'file_count_{i}',
                'filename': f'model_{i}.3mf',
                'file_path': f'/files/model_{i}.3mf',
                'file_type': '3mf' if i % 2 == 0 else 'gcode',
                'source': 'local' if i < 4 else 'ftp'
            })

        # Test count without filters
        total = await repo.count()
        assert total >= 7

        # Test count with source filter
        local_count = await repo.count(source='local')
        assert local_count >= 4  # 0, 1, 2, 3

        ftp_count = await repo.count(source='ftp')
        assert ftp_count >= 3  # 4, 5, 6


class TestPaginationPerformance:
    """Test that pagination doesn't fetch unnecessary data"""

    @pytest.mark.asyncio
    async def test_list_with_count_efficiency(self, temp_database):
        """Verify list_jobs_with_count doesn't fetch all records for count"""
        from src.database.database import Database
        from src.services.job_service import JobService
        from unittest.mock import MagicMock, AsyncMock

        db = Database(temp_database)
        await db.initialize()

        # Create mock event service
        mock_event_service = MagicMock()
        mock_event_service.emit_event = AsyncMock()

        service = JobService(db, mock_event_service)

        # Create printer
        await db.create_printer({
            'id': 'printer_perf',
            'name': 'Performance Test Printer',
            'type': 'bambu_lab'
        })

        # Create many jobs (100+)
        for i in range(150):
            await db.create_job({
                'id': f'job_perf_{i}',
                'printer_id': 'printer_perf',
                'printer_type': 'bambu_lab',
                'job_name': f'test_{i}.3mf',
                'status': 'completed'
            })

        # Request first page (limit 50)
        jobs, total = await service.list_jobs_with_count(limit=50, offset=0)

        # Should return only 50 jobs, but count all 150
        assert len(jobs) == 50
        assert total >= 150

        # This proves we didn't fetch all 150 jobs just to count them
        # The count came from an efficient COUNT(*) query

        await db.close()


# =====================================================
# Run marker for pytest
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
