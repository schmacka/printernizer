"""
Test suite for Database operations and German business logic
Tests database schema, constraints, triggers, and German business requirements.
"""
import pytest
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal


class TestDatabaseSchema:
    """Test database schema integrity and constraints"""
    
    def test_database_creation(self, temp_database):
        """Test database creation with schema"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Verify tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'configuration', 'download_history', 'files', 
            'jobs', 'printer_status_log', 'printers', 'system_events'
        ]
        
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_printer_table_constraints(self, db_connection):
        """Test printer table constraints and validation"""
        cursor = db_connection.cursor()
        
        # Test valid printer insertion
        cursor.execute("""
            INSERT INTO printers (id, name, type, ip_address, api_key, is_active)
            VALUES ('test_printer', 'Test Printer', 'prusa', '192.168.1.100', 'test_key', 1)
        """)
        db_connection.commit()
        
        # Test invalid printer type constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO printers (id, name, type, ip_address, is_active)
                VALUES ('invalid_printer', 'Invalid', 'invalid_type', '192.168.1.101', 1)
            """)
            db_connection.commit()
        
        # Test duplicate ID constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO printers (id, name, type, ip_address, is_active)
                VALUES ('test_printer', 'Duplicate', 'bambu_lab', '192.168.1.102', 1)
            """)
            db_connection.commit()
    
    def test_job_table_constraints(self, populated_database):
        """Test job table constraints and computed columns"""
        cursor = populated_database.cursor()
        
        # Test valid job insertion
        cursor.execute("""
            INSERT INTO jobs (printer_id, job_name, status, material_cost, power_cost, labor_cost)
            VALUES ('bambu_a1_001', 'constraint_test.3mf', 'queued', 1.25, 0.30, 7.50)
        """)
        populated_database.commit()
        
        # Verify computed total_cost column
        cursor.execute("""
            SELECT total_cost FROM jobs WHERE job_name = 'constraint_test.3mf'
        """)
        total_cost = cursor.fetchone()[0]
        assert total_cost == 9.05  # 1.25 + 0.30 + 7.50
        
        # Test invalid status constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status)
                VALUES ('bambu_a1_001', 'invalid_status.3mf', 'invalid_status')
            """)
            populated_database.commit()
        
        # Test invalid progress constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status, progress)
                VALUES ('bambu_a1_001', 'invalid_progress.3mf', 'printing', 150.0)
            """)
            populated_database.commit()
        
        # Test foreign key constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status)
                VALUES ('non_existent_printer', 'orphan_job.3mf', 'queued')
            """)
            populated_database.commit()
    
    def test_file_table_generated_columns(self, db_connection):
        """Test file table generated columns and status icons"""
        cursor = db_connection.cursor()
        
        test_cases = [
            ('available', '📁'),
            ('downloading', '⏬'),
            ('downloaded', '✓'),
            ('local', '💾'),
            ('error', '❌'),
            ('deleted', '🗑️')
        ]
        
        for i, (status, expected_icon) in enumerate(test_cases):
            cursor.execute("""
                INSERT INTO files (id, filename, file_type, file_size, download_status)
                VALUES (?, ?, '.3mf', 1024, ?)
            """, (f'test_file_{i}', f'test_{i}.3mf', status))
            
            # Verify generated status_icon
            cursor.execute("""
                SELECT status_icon FROM files WHERE id = ?
            """, (f'test_file_{i}',))
            
            actual_icon = cursor.fetchone()[0]
            assert actual_icon == expected_icon
        
        db_connection.commit()
    
    def test_database_indexes(self, temp_database):
        """Test that all required indexes exist"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Get all indexes
        cursor.execute("""
            SELECT name, tbl_name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        indexes = cursor.fetchall()
        
        # Verify key indexes exist
        expected_indexes = [
            'idx_printers_type',
            'idx_printers_status', 
            'idx_jobs_printer_id',
            'idx_jobs_status',
            'idx_files_download_status',
            'idx_files_printer_id'
        ]
        
        index_names = [idx[0] for idx in indexes]
        for expected in expected_indexes:
            assert expected in index_names
        
        conn.close()
    
    def test_database_triggers(self, populated_database):
        """Test database triggers for automatic updates"""
        cursor = populated_database.cursor()
        
        # Test printer updated_at trigger
        original_time = datetime.now()
        
        cursor.execute("""
            UPDATE printers SET name = 'Updated Printer Name' 
            WHERE id = 'bambu_a1_001'
        """)
        populated_database.commit()
        
        cursor.execute("""
            SELECT updated_at FROM printers WHERE id = 'bambu_a1_001'
        """)
        updated_time_str = cursor.fetchone()[0]
        updated_time = datetime.fromisoformat(updated_time_str)
        
        # updated_at should be newer than when we started
        assert updated_time >= original_time
    
    def test_job_status_change_trigger(self, populated_database):
        """Test job status change trigger creates system events"""
        cursor = populated_database.cursor()
        
        # Count existing system events
        cursor.execute("SELECT COUNT(*) FROM system_events")
        initial_count = cursor.fetchone()[0]
        
        # Update job status
        cursor.execute("""
            UPDATE jobs SET status = 'completed' 
            WHERE id = 1 AND status = 'printing'
        """)
        populated_database.commit()
        
        # Verify system event was created
        cursor.execute("SELECT COUNT(*) FROM system_events")
        new_count = cursor.fetchone()[0]
        
        assert new_count > initial_count
        
        # Verify event details
        cursor.execute("""
            SELECT event_type, title FROM system_events 
            WHERE job_id = 1 
            ORDER BY created_at DESC LIMIT 1
        """)
        result = cursor.fetchone()
        
        assert result[0] == 'job_complete'
        assert 'Job Status Changed' in result[1]
    
    def test_foreign_key_constraints(self, populated_database):
        """Test foreign key constraints are enforced"""
        cursor = populated_database.cursor()
        
        # Enable foreign key checks
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Try to delete printer with dependent jobs
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("DELETE FROM printers WHERE id = 'bambu_a1_001'")
            populated_database.commit()
        
        # Try to insert job with non-existent printer
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status)
                VALUES ('non_existent', 'test.3mf', 'queued')
            """)
            populated_database.commit()
    
    def test_database_views(self, populated_database):
        """Test database views provide correct data"""
        cursor = populated_database.cursor()
        
        # Test v_active_printers view
        cursor.execute("SELECT * FROM v_active_printers")
        active_printers = cursor.fetchall()
        
        assert len(active_printers) >= 2  # From sample data
        
        # Verify view includes printer info and current jobs
        printer = active_printers[0]
        assert 'id' in [desc[0] for desc in cursor.description]
        assert 'active_jobs' in [desc[0] for desc in cursor.description]
        
        # Test v_recent_jobs view
        cursor.execute("SELECT * FROM v_recent_jobs")
        recent_jobs = cursor.fetchall()
        
        assert len(recent_jobs) >= 2  # From sample data
        
        # Test v_file_statistics view
        cursor.execute("SELECT * FROM v_file_statistics")
        file_stats = cursor.fetchall()
        
        # Should have statistics for different download statuses
        assert len(file_stats) >= 1


class TestGermanBusinessLogic:
    """Test German business logic and requirements"""
    
    def test_european_timezone_handling(self, populated_database, test_utils):
        """Test that timestamps are handled with Europe/Berlin timezone"""
        cursor = populated_database.cursor()
        
        # Get configuration timezone
        cursor.execute("SELECT value FROM configuration WHERE key = 'system.timezone'")
        timezone_config = cursor.fetchone()[0]
        assert timezone_config == 'Europe/Berlin'
        
        # Test job creation with Berlin timezone
        berlin_time = test_utils.berlin_timestamp('2025-09-03T14:30:00')
        
        cursor.execute("""
            INSERT INTO jobs (printer_id, job_name, status, created_at)
            VALUES ('bambu_a1_001', 'timezone_test.3mf', 'queued', ?)
        """, (berlin_time.isoformat(),))
        populated_database.commit()
        
        # Verify timezone handling
        cursor.execute("""
            SELECT created_at FROM jobs WHERE job_name = 'timezone_test.3mf'
        """)
        stored_time = cursor.fetchone()[0]
        
        # Should store timestamp properly
        assert stored_time is not None
    
    def test_euro_currency_calculations(self, populated_database):
        """Test EUR currency calculations with German VAT"""
        cursor = populated_database.cursor()
        
        # Get VAT rate from configuration
        cursor.execute("SELECT value FROM configuration WHERE key = 'business.vat_rate'")
        vat_rate = float(cursor.fetchone()[0])
        assert vat_rate == 0.19  # 19% German VAT
        
        # Test cost calculation
        material_cost = 2.50  # EUR
        power_cost = 0.45     # EUR
        labor_cost = 12.00    # EUR
        
        cursor.execute("""
            INSERT INTO jobs (printer_id, job_name, status, material_cost, power_cost, labor_cost)
            VALUES ('bambu_a1_001', 'euro_test.3mf', 'completed', ?, ?, ?)
        """, (material_cost, power_cost, labor_cost))
        populated_database.commit()
        
        # Verify computed total
        cursor.execute("""
            SELECT total_cost FROM jobs WHERE job_name = 'euro_test.3mf'
        """)
        total_cost = cursor.fetchone()[0]
        
        expected_total = material_cost + power_cost + labor_cost
        assert abs(total_cost - expected_total) < 0.01
        
        # Calculate VAT for business invoice
        vat_amount = round(total_cost * vat_rate, 2)
        total_with_vat = total_cost + vat_amount
        
        # Verify German VAT calculation
        assert vat_amount == 2.84  # 19% of 14.95
        assert total_with_vat == 17.79
    
    def test_german_business_hours_config(self, populated_database):
        """Test German business hours configuration"""
        cursor = populated_database.cursor()
        
        # Verify business configuration exists
        business_configs = [
            ('business.mode', 'true'),
            ('business.currency', 'EUR'),
            ('business.vat_rate', '0.19'),
        ]
        
        for key, expected_value in business_configs:
            cursor.execute("SELECT value FROM configuration WHERE key = ?", (key,))
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == expected_value
    
    def test_material_cost_per_gram_tracking(self, populated_database):
        """Test material cost tracking per gram (German precision requirements)"""
        cursor = populated_database.cursor()
        
        # Get default material cost
        cursor.execute("""
            SELECT value FROM configuration 
            WHERE key = 'costs.default_material_cost_per_gram'
        """)
        default_cost = float(cursor.fetchone()[0])
        assert default_cost == 0.05  # 5 cents per gram
        
        # Test precise material calculations
        test_cases = [
            (25.5, 0.05, 1.275),   # 25.5g * 0.05 EUR/g = 1.275 EUR
            (100.0, 0.048, 4.80),  # 100g * 0.048 EUR/g = 4.80 EUR
            (15.75, 0.052, 0.819), # 15.75g * 0.052 EUR/g = 0.819 EUR
        ]
        
        for usage, cost_per_gram, expected_cost in test_cases:
            calculated_cost = round(usage * cost_per_gram, 3)
            assert abs(calculated_cost - expected_cost) < 0.001
    
    def test_power_cost_calculation_german_rates(self, populated_database):
        """Test power cost calculation with German electricity rates"""
        cursor = populated_database.cursor()
        
        # Get power rate from configuration
        cursor.execute("""
            SELECT value FROM configuration WHERE key = 'costs.power_rate_per_kwh'
        """)
        power_rate = float(cursor.fetchone()[0])
        assert power_rate == 0.30  # 30 cents per kWh (typical German rate)
        
        # Test power cost calculation
        test_cases = [
            (2.5, 0.3, 0.30, 0.225),   # 2.5h * 0.3kWh * 0.30 EUR/kWh = 0.225 EUR
            (4.0, 0.25, 0.30, 0.30),   # 4h * 0.25kWh * 0.30 EUR/kWh = 0.30 EUR
            (1.5, 0.4, 0.30, 0.18),    # 1.5h * 0.4kWh * 0.30 EUR/kWh = 0.18 EUR
        ]
        
        for hours, kwh_per_hour, rate, expected_cost in test_cases:
            calculated_cost = round(hours * kwh_per_hour * rate, 3)
            assert abs(calculated_cost - expected_cost) < 0.001
    
    def test_business_vs_private_job_tracking(self, populated_database):
        """Test business vs private job classification for German tax requirements"""
        cursor = populated_database.cursor()
        
        # Insert business job
        cursor.execute("""
            INSERT INTO jobs (printer_id, job_name, status, is_business, customer_name, 
                            material_cost, power_cost, labor_cost)
            VALUES ('bambu_a1_001', 'business_job.3mf', 'completed', 1, 'Mustermann GmbH',
                    5.25, 1.20, 15.00)
        """)
        
        # Insert private job
        cursor.execute("""
            INSERT INTO jobs (printer_id, job_name, status, is_business, 
                            material_cost, power_cost, labor_cost)
            VALUES ('bambu_a1_001', 'private_job.3mf', 'completed', 0,
                    2.10, 0.60, 0.00)
        """)
        
        populated_database.commit()
        
        # Verify business job tracking
        cursor.execute("""
            SELECT COUNT(*), SUM(total_cost) 
            FROM jobs WHERE is_business = 1
        """)
        business_count, business_total = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*), SUM(total_cost) 
            FROM jobs WHERE is_business = 0
        """)
        private_count, private_total = cursor.fetchone()
        
        # Should be able to track both separately for tax purposes
        assert business_count >= 1
        assert private_count >= 1
        assert business_total > private_total  # Business jobs typically more expensive
    
    def test_german_file_retention_policies(self, populated_database):
        """Test file retention policies according to German data protection"""
        cursor = populated_database.cursor()
        
        # Get retention configuration
        cursor.execute("""
            SELECT value FROM configuration WHERE key = 'files.cleanup_days'
        """)
        retention_days = int(cursor.fetchone()[0])
        assert retention_days == 90  # 90 days retention
        
        # Test file age calculation
        old_date = datetime.now() - timedelta(days=retention_days + 1)
        recent_date = datetime.now() - timedelta(days=retention_days - 1)
        
        # Insert old file (should be eligible for cleanup)
        cursor.execute("""
            INSERT INTO files (id, filename, file_type, file_size, download_status, downloaded_at)
            VALUES ('old_file', 'old_file.3mf', '.3mf', 1024, 'downloaded', ?)
        """, (old_date.isoformat(),))
        
        # Insert recent file (should be kept)
        cursor.execute("""
            INSERT INTO files (id, filename, file_type, file_size, download_status, downloaded_at)
            VALUES ('recent_file', 'recent_file.3mf', '.3mf', 1024, 'downloaded', ?)
        """, (recent_date.isoformat(),))
        
        populated_database.commit()
        
        # Query files eligible for cleanup
        cursor.execute("""
            SELECT COUNT(*) FROM files 
            WHERE download_status = 'downloaded' 
            AND downloaded_at < datetime('now', '-90 days')
        """)
        old_files_count = cursor.fetchone()[0]
        
        assert old_files_count >= 1  # Should find the old file


class TestDatabasePerformance:
    """Test database performance with large datasets"""
    
    def test_job_query_performance_with_indexes(self, db_connection):
        """Test that indexes improve query performance"""
        cursor = db_connection.cursor()
        
        # Insert many jobs
        for i in range(1000):
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status, is_business, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f'printer_{i % 5}',
                f'job_{i:04d}.3mf', 
                ['queued', 'printing', 'completed'][i % 3],
                i % 2 == 0,
                datetime.now().isoformat()
            ))
        
        db_connection.commit()
        
        # Test indexed queries should be fast
        import time
        
        # Query by status (indexed)
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'printing'")
        result = cursor.fetchone()
        query_time = time.time() - start_time
        
        assert result[0] > 0
        assert query_time < 0.1  # Should be very fast with index
        
        # Query by printer_id (indexed)
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE printer_id = 'printer_1'")
        result = cursor.fetchone()
        query_time = time.time() - start_time
        
        assert result[0] > 0
        assert query_time < 0.1  # Should be very fast with index
    
    def test_database_size_estimates(self, db_connection):
        """Test database size remains reasonable with realistic data"""
        cursor = db_connection.cursor()
        
        # Get initial database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        initial_size = cursor.fetchone()[0]
        
        # Insert realistic amount of data (6 months operation)
        # 2 printers, 10 jobs/day average, 50 files/week
        for i in range(1800):  # ~6 months of jobs
            cursor.execute("""
                INSERT INTO jobs (printer_id, job_name, status, material_cost, power_cost, labor_cost)
                VALUES (?, ?, 'completed', ?, ?, ?)
            """, (
                f'printer_{i % 2}',
                f'realistic_job_{i:04d}.3mf',
                round(i * 0.05 + 1.0, 2),  # Material cost 1-90 EUR
                round(i * 0.01 + 0.1, 2),  # Power cost
                round(i * 0.25 + 5.0, 2)   # Labor cost
            ))
        
        for i in range(300):  # 300 files
            cursor.execute("""
                INSERT INTO files (id, filename, file_type, file_size, download_status)
                VALUES (?, ?, '.3mf', ?, 'downloaded')
            """, (
                f'realistic_file_{i:04d}',
                f'file_{i:04d}.3mf',
                1024 * 1024 + i * 1000  # 1MB + variation
            ))
        
        db_connection.commit()
        
        # Get final database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        final_size = cursor.fetchone()[0]
        
        # Database should grow but remain reasonable (< 50MB for test data)
        size_growth_mb = (final_size - initial_size) / (1024 * 1024)
        assert size_growth_mb < 50  # Should be under 50MB for 6 months data