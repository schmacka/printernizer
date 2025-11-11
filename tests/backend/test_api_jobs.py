"""
Test suite for Job Management API endpoints
Tests all job-related API functionality including monitoring,
progress tracking, and German business calculations.
"""
import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timedelta, timezone
import sqlite3
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestJobAPI:
    """Test job management API endpoints"""
    
    def test_get_jobs_empty_database(self, client, temp_database):
        """Test GET /api/v1/jobs with empty database"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value.execute.return_value.fetchall.return_value = []
            
            response = client.get("/api/v1/jobs")
            
            assert response.status_code == 200
            data = response.json()
            assert data['jobs'] == []
            assert data['total_count'] == 0
            assert data['active_jobs'] == 0
            assert 'pagination' in data
    
    def test_get_jobs_with_data(self, client, populated_database):
        """Test GET /api/v1/jobs with existing jobs"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get("/api/v1/jobs")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['jobs']) == 2
            assert data['total_count'] == 2
            assert data['active_jobs'] == 1  # One printing job
            
            # Verify job structure
            printing_job = next(j for j in data['jobs'] if j['status'] == 'printing')
            assert printing_job['job_name'] == 'test_cube.3mf'
            assert printing_job['progress'] == 45.7
            assert printing_job['printer_name'] == 'Bambu Lab A1 #1'
            assert printing_job['is_business'] is True
            
            completed_job = next(j for j in data['jobs'] if j['status'] == 'completed')
            assert completed_job['quality_rating'] == 4
            assert completed_job['first_layer_adhesion'] == 'good'
    
    def test_get_jobs_filter_by_status(self, client, populated_database):
        """Test GET /api/v1/jobs?status=printing"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get("/api/v1/jobs?status=printing")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['jobs']) == 1
            assert data['jobs'][0]['status'] == 'printing'
    
    def test_get_jobs_filter_by_printer(self, client, populated_database):
        """Test GET /api/v1/jobs?printer_id=bambu_a1_001"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get("/api/v1/jobs?printer_id=bambu_a1_001")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['jobs']) == 1
            assert data['jobs'][0]['printer_id'] == 'bambu_a1_001'
    
    def test_get_jobs_filter_by_business_type(self, client, populated_database):
        """Test GET /api/v1/jobs?is_business=true"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get("/api/v1/jobs?is_business=true")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['jobs']) == 1
            assert data['jobs'][0]['is_business'] is True
            assert data['jobs'][0]['customer_name'] == 'Test Customer GmbH'
    
    def test_get_jobs_date_range_filter(self, client, populated_database):
        """Test GET /api/v1/jobs with date range filtering"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get(
                "/jobs?start_date={yesterday}&end_date={today}"
            )
            
            assert response.status_code == 200
            data = response.json()
            # Should return jobs within date range
            assert isinstance(data['jobs'], list)
    
    def test_get_jobs_pagination(self, client, populated_database):
        """Test GET /api/v1/jobs with pagination"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get("/api/v1/jobs?page=1&limit=1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['jobs']) == 1
            assert data['pagination']['current_page'] == 1
            assert data['pagination']['total_pages'] == 2
            assert data['pagination']['has_next'] is True
    
    def test_post_jobs_create_new_job(self, client, db_connection):
        """Test POST /api/v1/jobs - Create new print job"""
        job_data = {
            'printer_id': 'bambu_a1_001',
            'job_name': 'new_test_print.3mf',
            'file_path': '/uploads/new_test_print.3mf',
            'material_type': 'PLA',
            'material_brand': 'OVERTURE',
            'material_color': 'Red',
            'material_estimated_usage': 30.0,
            'material_cost_per_gram': 0.05,
            'layer_height': 0.2,
            'infill_percentage': 15,
            'nozzle_temperature': 210,
            'bed_temperature': 60,
            'estimated_duration': 9000,
            'is_business': True,
            'customer_name': 'New Customer GmbH',
            'customer_order_id': 'ORD-2025-001'
        }
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            
            response = client.post(
                "/jobs",
                json=job_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data['job']['job_name'] == job_data['job_name']
            assert data['job']['status'] == 'queued'
            assert data['job']['progress'] == 0.0
            assert 'id' in data['job']
            
            # Verify cost calculations
            expected_material_cost = job_data['material_estimated_usage'] * job_data['material_cost_per_gram']
            assert data['job']['material_cost'] == expected_material_cost
    
    def test_post_jobs_validation_errors(self, client):
        """Test POST /api/v1/jobs with validation errors"""
        test_cases = [
            # Missing required fields
            ({}, 400, 'Missing required field: printer_id'),
            ({'printer_id': 'test'}, 400, 'Missing required field: job_name'),
            
            # Invalid printer_id
            ({
                'printer_id': 'non_existent_printer',
                'job_name': 'test.3mf'
            }, 404, 'Printer not found'),
            
            # Invalid material usage
            ({
                'printer_id': 'bambu_a1_001',
                'job_name': 'test.3mf',
                'material_estimated_usage': -10.0
            }, 400, 'Material usage must be positive'),
            
            # Invalid temperature values
            ({
                'printer_id': 'bambu_a1_001',
                'job_name': 'test.3mf',
                'nozzle_temperature': 500
            }, 400, 'Nozzle temperature out of range'),
            
            # Invalid layer height
            ({
                'printer_id': 'bambu_a1_001',
                'job_name': 'test.3mf',
                'layer_height': 2.0
            }, 400, 'Layer height out of range')
        ]
        
        for job_data, expected_status, expected_error in test_cases:
            response = client.post(
                "/jobs",
                json=job_data
            )
            
            assert response.status_code == expected_status
            if expected_status in [400, 404]:
                assert expected_error in response.json()['error']['message']
    
    def test_get_job_details(self, client, populated_database):
        """Test GET /api/v1/jobs/{id} - Get specific job details"""
        job_id = 1  # From populated database
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.get("/api/v1/jobs/{job_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify complete job details
            job = data['job']
            assert job['id'] == job_id
            assert job['job_name'] == 'test_cube.3mf'
            assert job['status'] == 'printing'
            assert job['printer_info']['name'] == 'Bambu Lab A1 #1'
            
            # Verify material information
            assert job['material_type'] == 'PLA'
            assert job['material_brand'] == 'OVERTURE'
            assert job['material_estimated_usage'] == 25.5
            
            # Verify cost calculations
            assert 'material_cost' in job
            assert 'total_cost' in job
            
            # Verify timeline information
            assert 'estimated_duration' in job
            assert 'created_at' in job
    
    def test_get_job_details_not_found(self, client):
        """Test GET /api/v1/jobs/{id} for non-existent job"""
        response = client.get("/api/v1/jobs/99999")
        
        assert response.status_code == 404
        assert 'Job not found' in response.json()['error']['message']
    
    def test_put_job_status_update(self, client, populated_database):
        """Test PUT /api/v1/jobs/{id}/status - Update job status"""
        job_id = 1
        status_data = {
            'status': 'paused',
            'progress': 47.5,
            'layer_current': 156,
            'notes': 'Paused for material change'
        }
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.put(
                "/jobs/{job_id}/status",
                json=status_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['job']['status'] == 'paused'
            assert data['job']['progress'] == 47.5
            assert data['job']['layer_current'] == 156
            assert data['job']['notes'] == 'Paused for material change'
    
    def test_put_job_completion_with_quality_assessment(self, client, populated_database):
        """Test PUT /api/v1/jobs/{id}/status - Mark job as completed with quality assessment"""
        job_id = 1
        completion_data = {
            'status': 'completed',
            'progress': 100.0,
            'end_time': datetime.now().isoformat(),
            'quality_rating': 5,
            'first_layer_adhesion': 'excellent',
            'surface_finish': 'excellent',
            'dimensional_accuracy': 0.1,
            'actual_material_usage': 24.8,
            'notes': 'Perfect print quality achieved'
        }
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.put(
                "/jobs/{job_id}/status",
                json=completion_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['job']['status'] == 'completed'
            assert data['job']['quality_rating'] == 5
            assert data['job']['first_layer_adhesion'] == 'excellent'
            assert data['job']['actual_material_usage'] == 24.8
            
            # Verify cost recalculation with actual material usage
            expected_actual_cost = completion_data['actual_material_usage'] * 0.05  # From fixtures
            assert abs(data['job']['material_cost'] - expected_actual_cost) < 0.01
    
    def test_put_job_failure_handling(self, client, populated_database):
        """Test PUT /api/v1/jobs/{id}/status - Handle job failure"""
        job_id = 1
        failure_data = {
            'status': 'failed',
            'failure_reason': 'First layer adhesion failure',
            'end_time': datetime.now().isoformat(),
            'progress': 15.5,
            'layer_current': 51,
            'quality_rating': 1,
            'first_layer_adhesion': 'poor'
        }
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.put(
                "/jobs/{job_id}/status",
                json=failure_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['job']['status'] == 'failed'
            assert data['job']['failure_reason'] == 'First layer adhesion failure'
            assert data['job']['quality_rating'] == 1
    
    def test_put_job_status_invalid_transitions(self, client):
        """Test PUT /api/v1/jobs/{id}/status with invalid status transitions"""
        job_id = 2  # Completed job from fixtures
        
        test_cases = [
            # Cannot restart completed job
            ({'status': 'printing'}, 'Cannot change status from completed to printing'),
            
            # Invalid status values
            ({'status': 'invalid_status'}, 'Invalid job status'),
            
            # Cannot set negative progress
            ({'progress': -5.0}, 'Progress must be between 0 and 100'),
            
            # Cannot set progress over 100
            ({'progress': 105.0}, 'Progress must be between 0 and 100'),
        ]
        
        for status_data, expected_error in test_cases:
            response = client.put(
                "/jobs/{job_id}/status",
                json=status_data
            )
            
            assert response.status_code == 400
            assert expected_error in response.json()['error']['message']
    
    def test_delete_job(self, client, populated_database):
        """Test DELETE /api/v1/jobs/{id}"""
        job_id = 2  # Completed job can be deleted
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.delete("/jobs/{job_id}")
            
            assert response.status_code == 204
    
    def test_delete_active_job_forbidden(self, client, populated_database):
        """Test DELETE /api/v1/jobs/{id} - Cannot delete active job"""
        job_id = 1  # Active printing job
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            response = client.delete("/jobs/{job_id}")
            
            assert response.status_code == 409
            assert 'Cannot delete active job' in response.json()['error']['message']


class TestJobBusinessLogic:
    """Test job-related business logic and German requirements"""
    
    def test_german_cost_calculations(self, sample_cost_calculations, german_business_config):
        """Test cost calculations according to German business requirements"""
        # Material cost
        material_cost = sample_cost_calculations['material_usage_grams'] * \
                       sample_cost_calculations['material_cost_per_gram']
        
        # Power cost
        power_cost = sample_cost_calculations['print_duration_hours'] * \
                    sample_cost_calculations['power_consumption_kwh'] * \
                    sample_cost_calculations['power_rate_per_kwh']
        
        # Labor cost
        labor_cost = sample_cost_calculations['labor_hours'] * \
                    sample_cost_calculations['labor_rate_per_hour']
        
        # Subtotal
        subtotal = material_cost + power_cost + labor_cost
        
        # VAT calculation (German 19%)
        vat_rate = float(german_business_config['vat_rate'])
        vat_amount = round(subtotal * vat_rate, 2)
        
        # Total with VAT
        total_with_vat = round(subtotal + vat_amount, 2)
        
        # Verify calculations (using pytest.approx for floating point comparisons)
        assert material_cost == pytest.approx(1.275, abs=0.01)  # 25.5g * 0.05 EUR/g
        assert power_cost == pytest.approx(0.225, abs=0.01)     # 2.5h * 0.3kWh * 0.30 EUR/kWh
        assert labor_cost == pytest.approx(7.5, abs=0.01)       # 0.5h * 15.0 EUR/h
        assert subtotal == pytest.approx(9.0, abs=0.01)         # Sum of above
        assert vat_amount == pytest.approx(1.71, abs=0.01)      # 19% of 9.0 EUR
        assert total_with_vat == pytest.approx(10.71, abs=0.01) # 9.0 + 1.71 EUR
    
    def test_business_vs_private_job_classification(self, populated_database):
        """Test business vs private job classification"""
        cursor = populated_database.cursor()
        
        # Get business job
        cursor.execute("SELECT * FROM jobs WHERE is_business = 1")
        business_job = cursor.fetchone()
        assert business_job is not None
        assert business_job['customer_name'] == 'Test Customer GmbH'
        assert business_job['customer_order_id'] is None or len(business_job['customer_order_id']) > 0
        
        # Get private job
        cursor.execute("SELECT * FROM jobs WHERE is_business = 0")
        private_job = cursor.fetchone()
        assert private_job is not None
        assert private_job['customer_name'] is None or private_job['customer_name'] == ''
    
    def test_job_timezone_handling(self, populated_database, test_utils):
        """Test job timestamps use Europe/Berlin timezone"""
        cursor = populated_database.cursor()
        cursor.execute("SELECT created_at, start_time, end_time FROM jobs LIMIT 1")
        result = cursor.fetchone()
        
        if result['start_time']:
            berlin_time = test_utils.berlin_timestamp(result['start_time'])
            assert berlin_time.tzinfo.zone == 'Europe/Berlin'
    
    def test_material_usage_tracking(self, sample_job_data):
        """Test material usage tracking for German sustainability requirements"""
        job = sample_job_data[0]  # Business job with material data
        
        # Verify material tracking fields are present
        assert 'material_type' in job
        assert 'material_brand' in job
        assert 'material_estimated_usage' in job
        assert 'material_cost_per_gram' in job
        
        # Calculate material efficiency
        estimated_usage = job['material_estimated_usage']  # 25.5g
        if 'material_actual_usage' in job and job['material_actual_usage']:
            actual_usage = job['material_actual_usage']
            efficiency = (estimated_usage - actual_usage) / estimated_usage
            # Should be reasonably efficient (within 10%)
            assert abs(efficiency) < 0.10
    
    def test_print_quality_assessment_german_standards(self, sample_job_data):
        """Test print quality assessment according to German quality standards"""
        completed_job = sample_job_data[1]  # Completed job
        
        # Quality rating should be 1-5 scale
        quality_rating = completed_job.get('quality_rating')
        if quality_rating:
            assert 1 <= quality_rating <= 5
        
        # First layer adhesion categories
        adhesion = completed_job.get('first_layer_adhesion')
        if adhesion:
            assert adhesion in ['excellent', 'good', 'fair', 'poor']
        
        # Surface finish categories
        surface_finish = completed_job.get('surface_finish')
        if surface_finish:
            assert surface_finish in ['excellent', 'good', 'fair', 'poor']


class TestJobAPIPerformance:
    """Test job API performance and scalability"""
    
    def test_large_job_list_performance(self, client, db_connection):
        """Test API performance with large number of jobs"""
        cursor = db_connection.cursor()
        
        # Insert many jobs for performance testing
        for i in range(500):
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status, material_type, is_business)
                VALUES (?, ?, ?, ?, ?)
            """, (
                'test_printer_001',
                f'test_job_{i:03d}.3mf',
                'completed' if i % 2 else 'queued',
                'PLA',
                i % 3 == 0  # Every third job is business
            ))
        
        db_connection.commit()
        
        # Time the API request
        import time
        start_time = time.time()
        
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = db_connection
            response = client.get("/api/v1/jobs")
        
        end_time = time.time()
        request_time = end_time - start_time
        
        # Request should complete within reasonable time
        assert response.status_code == 200
        assert request_time < 2.0  # Should complete within 2 seconds
        
        data = response.json()
        assert data['total_count'] >= 500
    
    def test_job_filtering_performance(self, client, db_connection):
        """Test performance of job filtering operations"""
        # Test various filter combinations that should use database indexes
        filter_tests = [
            '?status=printing',
            '?is_business=true',
            '?printer_id=bambu_a1_001',
            '?status=completed&is_business=true',
            '?material_type=PLA',
        ]
        
        for filter_query in filter_tests:
            start_time = time.time()
            
            response = client.get("/api/v1/jobs{filter_query}")
            
            end_time = time.time()
            request_time = end_time - start_time
            
            assert response.status_code == 200
            assert request_time < 1.0  # Each filtered query should be fast
    
    def test_concurrent_job_updates(self, client, populated_database):
        """Test concurrent job status updates"""
        import threading
        import time
        
        results = []
        
        def update_job_status(job_id, status):
            try:
                response = client.put(
                    "/jobs/{job_id}/status",
                    json={'status': status, 'progress': 50.0}
                )
                results.append(response.status_code)
            except Exception as e:
                results.append(500)  # Error case
        
        # Create multiple threads updating different jobs
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_job_status, args=(1, 'printing'))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # At least some requests should succeed (depends on implementation)
        success_count = len([r for r in results if r == 200])
        assert success_count >= 1  # At least one should succeed


class TestJobAPIErrorHandling:
    """Test error handling and edge cases for job API"""
    
    def test_job_api_database_connection_error(self, client):
        """Test job API behavior when database is unavailable"""
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.side_effect = sqlite3.OperationalError("database is locked")
            
            response = client.get("/api/v1/jobs")
            
            assert response.status_code == 500
            error_data = response.json()
            assert 'Database error' in error_data['error']['message']
    
    def test_job_creation_with_invalid_printer(self, client):
        """Test job creation with non-existent printer"""
        job_data = {
            'printer_id': 'non_existent_printer_123',
            'job_name': 'test.3mf'
        }
        
        response = client.post(
            "/jobs",
            json=job_data
        )
        
        assert response.status_code == 404
        assert 'Printer not found' in response.json()['error']['message']
    
    def test_job_update_race_condition_handling(self, client, populated_database):
        """Test handling of race conditions in job updates"""
        job_id = 1
        
        # Simulate concurrent updates by patching the database update
        with patch('src.database.database.Database.get_connection') as mock_db:
            mock_db.return_value = populated_database
            
            # First update
            response1 = client.put(
                "/jobs/{job_id}/status",
                json={'status': 'paused', 'progress': 30.0}
            )
            
            # Second update (simulating race condition)
            response2 = client.put(
                "/jobs/{job_id}/status",
                json={'status': 'printing', 'progress': 35.0}
            )
            
            # Both updates should be handled gracefully
            assert response1.status_code in [200, 409]  # OK or Conflict
            assert response2.status_code in [200, 409]  # OK or Conflict
    
    def test_job_deletion_safety_checks(self, client, populated_database):
        """Test safety checks when deleting jobs"""
        # Try to delete job that doesn't exist
        response = client.delete("/jobs/99999")
        assert response.status_code == 404
        
        # Try to delete active job (should be prevented)
        active_job_id = 1  # Printing job from fixtures
        response = client.delete("/jobs/{active_job_id}")
        assert response.status_code == 409