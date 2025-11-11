"""
Performance and Load Tests for Printernizer Phase 1
Tests system performance under various load conditions including:
- Multiple concurrent printers
- High-frequency status updates
- Large file downloads
- Database performance under load
- WebSocket connection scaling
- Memory usage optimization
"""
import pytest
import asyncio
import time
import threading
import sqlite3
import tempfile
import json
import psutil
import concurrent.futures
from datetime import datetime, timezone
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from dataclasses import dataclass
from typing import List, Dict, Any
import memory_profiler


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results"""
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    requests_per_second: float
    success_rate_percent: float
    error_count: int
    max_response_time_ms: float
    min_response_time_ms: float
    avg_response_time_ms: float


class PerformanceTestBase:
    """Base class for performance tests with common utilities"""
    
    def measure_performance(self, func, *args, **kwargs):
        """Measure performance metrics for a function execution"""
        process = psutil.Process()
        
        # Initial measurements
        start_time = time.perf_counter()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        # Final measurements
        end_time = time.perf_counter()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()
        
        execution_time_ms = (end_time - start_time) * 1000
        memory_usage_mb = end_memory - start_memory
        cpu_usage_percent = end_cpu - start_cpu
        
        return {
            'result': result,
            'success': success,
            'error': error,
            'execution_time_ms': execution_time_ms,
            'memory_usage_mb': memory_usage_mb,
            'cpu_usage_percent': cpu_usage_percent
        }
    
    async def load_test(self, async_func, concurrent_requests: int, total_requests: int):
        """Execute load test with concurrent requests"""
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def bounded_request():
            async with semaphore:
                return await async_func()
        
        start_time = time.perf_counter()
        
        tasks = [bounded_request() for _ in range(total_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        success_rate = (successful / len(results)) * 100
        rps = len(results) / total_time
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful,
            'failed_requests': failed,
            'success_rate_percent': success_rate,
            'requests_per_second': rps,
            'total_time_seconds': total_time,
            'avg_request_time_ms': (total_time / len(results)) * 1000
        }


class TestDatabasePerformance(PerformanceTestBase):
    """Test database performance under various loads"""
    
    def test_large_dataset_queries(self, temp_database, performance_test_data):
        """Test database performance with large datasets"""
        conn = sqlite3.connect(temp_database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Insert large dataset (1000 jobs, 500 printers, 2000 files)
        large_job_count = performance_test_data['large_job_count']
        
        def insert_large_dataset():
            # Insert printers
            printers = []
            for i in range(100):
                printers.append((
                    f'perf_printer_{i:03d}',
                    f'Performance Test Printer {i}',
                    'bambu_lab' if i % 2 == 0 else 'prusa',
                    'A1' if i % 2 == 0 else 'Core One',
                    f'192.168.1.{100 + i}',
                    'active'
                ))
            
            cursor.executemany("""
                INSERT INTO printers (id, name, type, model, ip_address, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, printers)
            
            # Insert jobs
            jobs = []
            for i in range(large_job_count):
                printer_id = f'perf_printer_{i % 100:03d}'
                jobs.append((
                    f'perf_job_{i:04d}',
                    printer_id,
                    f'performance_test_job_{i}.3mf',
                    'printing' if i % 4 != 0 else 'completed',
                    float(i % 100),
                    datetime.now().isoformat(),
                    i % 2 == 0  # is_business
                ))
            
            cursor.executemany("""
                INSERT INTO jobs (id, printer_id, job_name, status, progress, created_at, is_business)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, jobs)
            
            conn.commit()
        
        # Measure insertion performance
        insert_metrics = self.measure_performance(insert_large_dataset)
        
        assert insert_metrics['execution_time_ms'] < 5000  # Should complete within 5 seconds
        assert insert_metrics['success'] is True
        
        # Test complex query performance
        def complex_query():
            return cursor.execute("""
                SELECT 
                    p.name as printer_name,
                    COUNT(j.id) as total_jobs,
                    AVG(j.progress) as avg_progress,
                    SUM(CASE WHEN j.status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                    SUM(CASE WHEN j.is_business = 1 THEN 1 ELSE 0 END) as business_jobs
                FROM printers p
                LEFT JOIN jobs j ON p.id = j.printer_id
                GROUP BY p.id, p.name
                HAVING COUNT(j.id) > 5
                ORDER BY completed_jobs DESC
                LIMIT 20
            """).fetchall()
        
        query_metrics = self.measure_performance(complex_query)
        
        assert query_metrics['execution_time_ms'] < 1000  # Complex query under 1 second
        assert len(query_metrics['result']) <= 20
        
        conn.close()
    
    def test_concurrent_database_access(self, temp_database):
        """Test database performance under concurrent access"""
        def database_worker(worker_id: int, operations: int):
            """Simulate concurrent database operations"""
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            results = []
            
            for i in range(operations):
                try:
                    # Mix of read and write operations
                    if i % 3 == 0:  # Read operation
                        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'printing'")
                        result = cursor.fetchone()[0]
                        results.append(('read', result, True))
                    
                    elif i % 3 == 1:  # Update operation
                        cursor.execute("""
                            UPDATE jobs SET progress = ? WHERE id LIKE 'perf_job_%' LIMIT 1
                        """, (float(i % 100),))
                        conn.commit()
                        results.append(('update', cursor.rowcount, True))
                    
                    else:  # Insert operation
                        cursor.execute("""
                            INSERT INTO jobs (id, printer_id, job_name, status, progress, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            f'worker_{worker_id}_job_{i}',
                            'perf_printer_001',
                            f'concurrent_test_{worker_id}_{i}.3mf',
                            'queued',
                            0.0,
                            datetime.now().isoformat()
                        ))
                        conn.commit()
                        results.append(('insert', cursor.lastrowid, True))
                
                except Exception as e:
                    results.append(('error', str(e), False))
            
            conn.close()
            return results
        
        # Run concurrent workers
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(database_worker, worker_id, 50)
                for worker_id in range(10)
            ]
            
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        # Analyze results
        successful_ops = sum(1 for _, _, success in all_results if success)
        failed_ops = len(all_results) - successful_ops
        ops_per_second = len(all_results) / execution_time
        
        assert execution_time < 30  # Should complete within 30 seconds
        assert successful_ops / len(all_results) > 0.95  # 95% success rate
        assert ops_per_second > 10  # At least 10 operations per second
    
    @pytest.mark.benchmark
    def test_database_indexing_performance(self, temp_database):
        """Test impact of database indexing on query performance"""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Insert test data without indexes
        test_jobs = [(f'idx_test_{i}', f'printer_{i % 50}', f'job_{i}.3mf', 
                     'completed' if i % 4 == 0 else 'printing', 
                     float(i % 100), datetime.now().isoformat())
                    for i in range(5000)]
        
        cursor.executemany("""
            INSERT INTO jobs (id, printer_id, job_name, status, progress, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, test_jobs)
        conn.commit()
        
        # Test query performance without indexes
        def query_without_index():
            return cursor.execute("""
                SELECT printer_id, COUNT(*) as job_count, AVG(progress) as avg_progress
                FROM jobs
                WHERE status = 'printing' AND progress > 50
                GROUP BY printer_id
                ORDER BY job_count DESC
            """).fetchall()
        
        no_index_metrics = self.measure_performance(query_without_index)
        
        # Add indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_printer_status ON jobs(printer_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_progress ON jobs(progress)")
        
        # Test query performance with indexes
        with_index_metrics = self.measure_performance(query_without_index)
        
        # Indexes should improve performance significantly
        performance_improvement = no_index_metrics['execution_time_ms'] / with_index_metrics['execution_time_ms']
        assert performance_improvement > 2  # At least 2x improvement
        
        conn.close()


class TestAPIPerformance(PerformanceTestBase):
    """Test API endpoint performance under load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, api_client, populated_database, test_config):
        """Test API performance with concurrent requests"""
        
        async def api_request():
            """Simulate API request"""
            with patch('src.database.database.Database.get_connection') as mock_db:
                mock_db.return_value = populated_database
                
                try:
                    response = api_client.get(f"{test_config['api_base_url']}/printers")
                    return {
                        'status_code': response.status_code,
                        'success': response.status_code == 200,
                        'response_time': response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else 0
                    }
                except Exception as e:
                    return {
                        'status_code': 500,
                        'success': False,
                        'error': str(e),
                        'response_time': 0
                    }
        
        # Load test with increasing concurrency
        concurrency_levels = [1, 5, 10, 25, 50]
        results = {}
        
        for concurrent in concurrency_levels:
            total_requests = concurrent * 10  # 10 requests per concurrent user
            
            load_result = await self.load_test(api_request, concurrent, total_requests)
            
            results[concurrent] = load_result
            
            # Performance assertions
            assert load_result['success_rate_percent'] > 95  # 95% success rate
            assert load_result['requests_per_second'] > concurrent * 0.5  # Reasonable throughput
        
        # Verify scalability
        rps_1_user = results[1]['requests_per_second']
        rps_10_users = results[10]['requests_per_second']
        
        # Should handle 10x users with reasonable performance degradation
        assert rps_10_users > rps_1_user * 3  # At least 3x throughput increase
    
    def test_large_response_performance(self, api_client, test_config):
        """Test API performance with large response payloads"""
        
        def create_large_dataset_response():
            """Create large dataset for response testing"""
            large_printer_list = {
                'printers': [
                    {
                        'id': f'load_test_printer_{i:04d}',
                        'name': f'Load Test Printer {i}',
                        'type': 'bambu_lab' if i % 2 == 0 else 'prusa',
                        'model': 'A1' if i % 2 == 0 else 'Core One',
                        'status': 'online' if i % 3 == 0 else 'offline',
                        'ip_address': f'192.168.{(i // 255) % 255}.{i % 255}',
                        'current_job': {
                            'job_name': f'large_dataset_job_{i}.3mf',
                            'progress': float(i % 100),
                            'status': 'printing'
                        } if i % 4 == 0 else None,
                        'statistics': {
                            'total_jobs': i * 3,
                            'completed_jobs': i * 2,
                            'failed_jobs': i // 10,
                            'total_print_time_hours': float(i * 5.5),
                            'material_used_kg': float(i * 0.25)
                        }
                    }
                    for i in range(1000)  # 1000 printers
                ],
                'total_count': 1000,
                'pagination': {
                    'page': 1,
                    'per_page': 1000,
                    'total_pages': 1
                },
                'summary': {
                    'online_printers': 334,
                    'printing_printers': 250,
                    'idle_printers': 84,
                    'offline_printers': 666
                }
            }
            return large_printer_list
        
        # Test response generation performance
        generation_metrics = self.measure_performance(create_large_dataset_response)
        
        assert generation_metrics['execution_time_ms'] < 500  # Generate within 500ms
        assert generation_metrics['memory_usage_mb'] < 100   # Keep memory usage reasonable
        
        # Test JSON serialization performance
        large_data = generation_metrics['result']
        
        def serialize_response():
            return json.dumps(large_data)
        
        serialization_metrics = self.measure_performance(serialize_response)
        
        assert serialization_metrics['execution_time_ms'] < 200  # Serialize within 200ms
        
        # Estimate response size
        json_size_mb = len(serialization_metrics['result']) / 1024 / 1024
        assert json_size_mb < 50  # Keep response size reasonable
    
    @pytest.mark.asyncio
    async def test_websocket_performance(self, mock_websocket):
        """Test WebSocket performance under high message frequency"""
        
        class WebSocketLoadTester:
            def __init__(self):
                self.messages_sent = 0
                self.messages_received = 0
                self.start_time = None
                self.end_time = None
            
            async def send_high_frequency_updates(self, messages_per_second: int, duration_seconds: int):
                """Send high-frequency updates to test WebSocket performance"""
                self.start_time = time.perf_counter()
                interval = 1.0 / messages_per_second
                total_messages = messages_per_second * duration_seconds
                
                for i in range(total_messages):
                    message = {
                        'type': 'job_progress',
                        'data': {
                            'job_id': f'perf_test_job_{i % 100}',
                            'progress': float(i % 100),
                            'layer_current': i % 300,
                            'estimated_time_remaining': 3600 - (i * 10)
                        }
                    }
                    
                    await mock_websocket.send(json.dumps(message))
                    self.messages_sent += 1
                    
                    # Simulate message processing delay
                    await asyncio.sleep(interval)
                
                self.end_time = time.perf_counter()
            
            def get_performance_metrics(self):
                if self.start_time and self.end_time:
                    duration = self.end_time - self.start_time
                    return {
                        'messages_sent': self.messages_sent,
                        'duration_seconds': duration,
                        'messages_per_second': self.messages_sent / duration,
                        'average_latency_ms': (duration / self.messages_sent) * 1000 if self.messages_sent > 0 else 0
                    }
                return {}
        
        # Test different message frequencies
        frequency_tests = [
            (10, 5),   # 10 msg/sec for 5 seconds
            (50, 3),   # 50 msg/sec for 3 seconds
            (100, 2),  # 100 msg/sec for 2 seconds
        ]
        
        for msg_per_sec, duration in frequency_tests:
            tester = WebSocketLoadTester()
            
            await tester.send_high_frequency_updates(msg_per_sec, duration)
            metrics = tester.get_performance_metrics()
            
            # Performance assertions
            assert metrics['messages_per_second'] >= msg_per_sec * 0.8  # At least 80% of target rate
            assert metrics['average_latency_ms'] < 100  # Keep latency under 100ms
            
            expected_messages = msg_per_sec * duration
            assert abs(metrics['messages_sent'] - expected_messages) <= 5  # Allow small variance


class TestFileDownloadPerformance(PerformanceTestBase):
    """Test file download and processing performance"""
    
    def test_large_file_download_performance(self, temp_download_directory):
        """Test performance when downloading large 3D model files"""
        
        def simulate_large_file_download(file_size_mb: int):
            """Simulate downloading a large file"""
            import os
            
            # Create mock large file data
            chunk_size = 1024 * 1024  # 1MB chunks
            total_chunks = file_size_mb
            
            file_path = os.path.join(temp_download_directory, f'large_file_{file_size_mb}mb.3mf')
            
            start_time = time.perf_counter()
            
            with open(file_path, 'wb') as f:
                for chunk_num in range(total_chunks):
                    # Simulate network delay
                    time.sleep(0.01)  # 10ms per MB (simulating 100 MB/s network)
                    
                    # Write chunk
                    chunk_data = b'0' * chunk_size
                    f.write(chunk_data)
            
            end_time = time.perf_counter()
            
            # Verify file size
            actual_size_mb = os.path.getsize(file_path) / 1024 / 1024
            
            return {
                'file_path': file_path,
                'expected_size_mb': file_size_mb,
                'actual_size_mb': actual_size_mb,
                'download_time_seconds': end_time - start_time,
                'download_speed_mbps': actual_size_mb / (end_time - start_time)
            }
        
        # Test different file sizes
        file_sizes = [10, 50, 100, 250]  # MB
        
        for size_mb in file_sizes:
            result = simulate_large_file_download(size_mb)
            
            # Performance assertions
            assert abs(result['actual_size_mb'] - result['expected_size_mb']) < 1  # Size accuracy
            assert result['download_speed_mbps'] > 50  # Minimum 50 MB/s effective rate
            assert result['download_time_seconds'] < size_mb * 0.5  # Max 0.5 seconds per MB
    
    def test_concurrent_file_downloads(self, temp_download_directory):
        """Test performance with multiple concurrent file downloads"""
        
        def download_worker(worker_id: int, file_count: int):
            """Simulate concurrent file downloads"""
            import os
            results = []
            
            for file_num in range(file_count):
                file_size_kb = 1024 + (file_num * 512)  # Variable file sizes
                file_path = os.path.join(temp_download_directory, 
                                       f'concurrent_download_{worker_id}_{file_num}.stl')
                
                start_time = time.perf_counter()
                
                # Simulate file download
                with open(file_path, 'wb') as f:
                    f.write(b'0' * (file_size_kb * 1024))
                
                end_time = time.perf_counter()
                
                results.append({
                    'worker_id': worker_id,
                    'file_num': file_num,
                    'file_size_kb': file_size_kb,
                    'download_time_ms': (end_time - start_time) * 1000
                })
                
                # Small delay between downloads
                time.sleep(0.05)
            
            return results
        
        # Run concurrent downloads
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(download_worker, worker_id, 5)
                for worker_id in range(8)
            ]
            
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze results
        total_files = len(all_results)
        total_size_mb = sum(r['file_size_kb'] for r in all_results) / 1024
        average_download_time_ms = sum(r['download_time_ms'] for r in all_results) / total_files
        files_per_second = total_files / total_time
        
        # Performance assertions
        assert total_time < 30  # Complete within 30 seconds
        assert files_per_second > 1  # At least 1 file per second overall
        assert average_download_time_ms < 500  # Average under 500ms per file


class TestMemoryAndResourceUsage(PerformanceTestBase):
    """Test memory usage and resource optimization"""
    
    @memory_profiler.profile
    def test_memory_usage_under_load(self, populated_database):
        """Test memory usage patterns under various load conditions"""
        
        def simulate_heavy_workload():
            """Simulate heavy workload to test memory usage"""
            # Simulate multiple concurrent operations
            data_structures = []
            
            # Create large data structures
            for i in range(100):
                large_dict = {
                    f'printer_{j}': {
                        'status': 'online',
                        'jobs': [f'job_{k}' for k in range(50)],
                        'files': [f'file_{k}.3mf' for k in range(25)],
                        'statistics': {'metric_{}'.format(m): float(m * i) for m in range(20)}
                    }
                    for j in range(50)
                }
                data_structures.append(large_dict)
            
            # Process data structures
            processed_data = []
            for data_dict in data_structures:
                processed = {}
                for printer_id, printer_data in data_dict.items():
                    processed[printer_id] = {
                        'job_count': len(printer_data['jobs']),
                        'file_count': len(printer_data['files']),
                        'avg_metric': sum(printer_data['statistics'].values()) / len(printer_data['statistics'])
                    }
                processed_data.append(processed)
            
            return processed_data
        
        # Measure memory usage
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        result = simulate_heavy_workload()
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clean up
        del result
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_recovered = peak_memory - final_memory
        
        # Memory usage assertions
        assert memory_increase < 500  # Don't use more than 500MB additional
        assert memory_recovered > memory_increase * 0.7  # Recover at least 70% of memory
    
    def test_database_connection_pooling_performance(self, temp_database):
        """Test database connection pooling efficiency"""
        
        class DatabaseConnectionPool:
            def __init__(self, max_connections=10):
                self.max_connections = max_connections
                self.available_connections = []
                self.active_connections = []
                self.db_path = temp_database
                
                # Initialize pool
                for _ in range(max_connections):
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    self.available_connections.append(conn)
            
            def get_connection(self):
                if self.available_connections:
                    conn = self.available_connections.pop()
                    self.active_connections.append(conn)
                    return conn
                else:
                    raise Exception("No available connections")
            
            def return_connection(self, conn):
                if conn in self.active_connections:
                    self.active_connections.remove(conn)
                    self.available_connections.append(conn)
            
            def close_all(self):
                for conn in self.available_connections + self.active_connections:
                    conn.close()
        
        # Test connection pool performance
        pool = DatabaseConnectionPool(max_connections=20)
        
        def database_operation_with_pool():
            """Simulate database operations using connection pool"""
            conn = pool.get_connection()
            try:
                cursor = conn.cursor()
                
                # Perform some database operations
                cursor.execute("SELECT COUNT(*) FROM jobs")
                result = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM printers WHERE status = 'online'")
                online_printers = cursor.fetchone()[0]
                
                return {'total_jobs': result, 'online_printers': online_printers}
                
            finally:
                pool.return_connection(conn)
        
        # Test pool performance vs individual connections
        start_time = time.perf_counter()
        
        # Using connection pool
        pool_results = []
        for _ in range(100):
            result = database_operation_with_pool()
            pool_results.append(result)
        
        pool_time = time.perf_counter() - start_time
        
        # Test individual connections (for comparison)
        start_time = time.perf_counter()
        
        individual_results = []
        for _ in range(100):
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM printers WHERE status = 'online'")
            online_printers = cursor.fetchone()[0]
            
            individual_results.append({'total_jobs': total_jobs, 'online_printers': online_printers})
            conn.close()
        
        individual_time = time.perf_counter() - start_time
        
        pool.close_all()
        
        # Performance comparison
        performance_improvement = individual_time / pool_time
        
        assert performance_improvement > 1.5  # Pool should be at least 50% faster
        assert len(pool_results) == len(individual_results)
    
    def test_cpu_usage_optimization(self):
        """Test CPU usage under various computational loads"""
        
        def cpu_intensive_task(complexity_level: int):
            """Simulate CPU-intensive tasks (e.g., 3D file processing)"""
            import math
            
            result = 0
            iterations = complexity_level * 10000
            
            for i in range(iterations):
                # Simulate complex mathematical operations
                result += math.sin(i) * math.cos(i) * math.sqrt(i + 1)
                
                # Simulate data processing
                if i % 1000 == 0:
                    data = {'iteration': i, 'result': result, 'timestamp': time.time()}
                    # Process data (simulate JSON serialization)
                    json.dumps(data)
            
            return result
        
        # Test CPU usage at different complexity levels
        complexity_levels = [1, 5, 10]  # Low, medium, high complexity
        
        for level in complexity_levels:
            process = psutil.Process()
            
            # Measure CPU usage
            start_cpu = process.cpu_percent()
            start_time = time.perf_counter()
            
            result = cpu_intensive_task(level)
            
            end_time = time.perf_counter()
            end_cpu = process.cpu_percent()
            
            execution_time = end_time - start_time
            cpu_usage = end_cpu - start_cpu
            
            # Performance assertions based on complexity
            if level == 1:  # Low complexity
                assert execution_time < 1.0  # Under 1 second
                assert cpu_usage < 80  # Reasonable CPU usage
            elif level == 5:  # Medium complexity
                assert execution_time < 5.0  # Under 5 seconds
                assert cpu_usage < 90  # Higher but manageable CPU usage
            else:  # High complexity
                assert execution_time < 15.0  # Under 15 seconds
                # High CPU usage is acceptable for intensive tasks
            
            assert result != 0  # Ensure computation actually occurred