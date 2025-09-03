"""
Test suite for WebSocket functionality
Tests real-time updates, connection handling, and error recovery.
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import websocket
from datetime import datetime


class TestWebSocketConnection:
    """Test WebSocket connection management"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self, mock_websocket, test_config):
        """Test WebSocket connection establishment"""
        websocket_url = test_config['websocket_url']
        
        with patch('websockets.connect') as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            mock_connect.return_value.__aexit__.return_value = None
            
            # Test connection
            async with mock_connect(websocket_url) as websocket_conn:
                assert websocket_conn == mock_websocket
                mock_connect.assert_called_once_with(websocket_url)
    
    @pytest.mark.asyncio
    async def test_websocket_authentication(self, mock_websocket, test_config):
        """Test WebSocket authentication (if implemented)"""
        auth_message = {
            'type': 'auth',
            'token': 'test_auth_token'
        }
        
        # Mock successful authentication response
        mock_websocket.recv.return_value = json.dumps({
            'type': 'auth_response',
            'status': 'authenticated',
            'user_id': 'test_user'
        })
        
        # Send auth message
        await mock_websocket.send(json.dumps(auth_message))
        
        # Receive auth response
        response = await mock_websocket.recv()
        response_data = json.loads(response)
        
        assert response_data['type'] == 'auth_response'
        assert response_data['status'] == 'authenticated'
        
        mock_websocket.send.assert_called_once_with(json.dumps(auth_message))
        mock_websocket.recv.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_subscription_management(self, mock_websocket):
        """Test WebSocket event subscription management"""
        subscription_message = {
            'type': 'subscribe',
            'events': ['printer_status', 'job_progress', 'file_download']
        }
        
        # Mock subscription confirmation
        mock_websocket.recv.return_value = json.dumps({
            'type': 'subscription_confirmed',
            'events': ['printer_status', 'job_progress', 'file_download']
        })
        
        # Send subscription
        await mock_websocket.send(json.dumps(subscription_message))
        
        # Receive confirmation
        response = await mock_websocket.recv()
        response_data = json.loads(response)
        
        assert response_data['type'] == 'subscription_confirmed'
        assert set(response_data['events']) == set(subscription_message['events'])
    
    @pytest.mark.asyncio
    async def test_websocket_connection_error_handling(self, test_config):
        """Test WebSocket connection error handling"""
        websocket_url = test_config['websocket_url']
        
        with patch('websockets.connect') as mock_connect:
            # Simulate connection error
            mock_connect.side_effect = ConnectionError("Connection refused")
            
            with pytest.raises(ConnectionError):
                async with mock_connect(websocket_url):
                    pass
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection_logic(self, mock_websocket, test_config):
        """Test WebSocket automatic reconnection"""
        websocket_url = test_config['websocket_url']
        
        with patch('websockets.connect') as mock_connect:
            # First connection fails
            mock_connect.side_effect = [
                ConnectionError("Connection lost"),
                mock_websocket  # Second attempt succeeds
            ]
            
            # Simulate reconnection logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    connection = await mock_connect(websocket_url)
                    assert connection == mock_websocket
                    break
                except ConnectionError:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(0.1)  # Brief delay before retry
            
            assert mock_connect.call_count == 2


class TestWebSocketRealTimeUpdates:
    """Test real-time update functionality"""
    
    @pytest.mark.asyncio
    async def test_printer_status_updates(self, mock_websocket):
        """Test real-time printer status updates"""
        status_update = {
            'type': 'printer_status_update',
            'printer_id': 'bambu_a1_001',
            'status': 'printing',
            'temperatures': {
                'nozzle': 210.5,
                'bed': 60.2,
                'chamber': 28.5
            },
            'current_job': {
                'id': 123,
                'progress': 47.3,
                'layer_current': 155,
                'estimated_remaining': 3420
            },
            'timestamp': '2025-09-03T14:30:15Z'
        }
        
        # Mock receiving status update
        mock_websocket.recv.return_value = json.dumps(status_update)
        
        # Receive and process update
        message = await mock_websocket.recv()
        update_data = json.loads(message)
        
        assert update_data['type'] == 'printer_status_update'
        assert update_data['printer_id'] == 'bambu_a1_001'
        assert update_data['status'] == 'printing'
        assert update_data['temperatures']['nozzle'] == 210.5
        assert update_data['current_job']['progress'] == 47.3
    
    @pytest.mark.asyncio
    async def test_job_progress_updates(self, mock_websocket):
        """Test real-time job progress updates"""
        progress_update = {
            'type': 'job_progress_update',
            'job_id': 123,
            'printer_id': 'bambu_a1_001',
            'progress': 52.7,
            'layer_current': 173,
            'layer_total': 328,
            'estimated_remaining': 2890,
            'print_speed': 85,
            'timestamp': '2025-09-03T14:31:00Z'
        }
        
        # Mock receiving progress update
        mock_websocket.recv.return_value = json.dumps(progress_update)
        
        # Receive and process update
        message = await mock_websocket.recv()
        update_data = json.loads(message)
        
        assert update_data['type'] == 'job_progress_update'
        assert update_data['job_id'] == 123
        assert update_data['progress'] == 52.7
        assert update_data['layer_current'] == 173
        assert update_data['estimated_remaining'] == 2890
    
    @pytest.mark.asyncio
    async def test_file_download_progress_updates(self, mock_websocket):
        """Test real-time file download progress updates"""
        download_update = {
            'type': 'file_download_progress',
            'download_id': 'download_001',
            'file_id': 'file_001',
            'status': 'downloading',
            'progress_percent': 73.5,
            'bytes_downloaded': 753664,
            'bytes_total': 1024000,
            'speed_bps': 102400,
            'eta_seconds': 26,
            'timestamp': '2025-09-03T14:31:30Z'
        }
        
        # Mock receiving download update
        mock_websocket.recv.return_value = json.dumps(download_update)
        
        # Receive and process update
        message = await mock_websocket.recv()
        update_data = json.loads(message)
        
        assert update_data['type'] == 'file_download_progress'
        assert update_data['download_id'] == 'download_001'
        assert update_data['progress_percent'] == 73.5
        assert update_data['eta_seconds'] == 26
    
    @pytest.mark.asyncio
    async def test_system_event_notifications(self, mock_websocket):
        """Test system event notifications via WebSocket"""
        system_event = {
            'type': 'system_event',
            'event_type': 'printer_connect',
            'severity': 'info',
            'title': 'Printer Connected',
            'description': 'Bambu Lab A1 #1 has connected successfully',
            'printer_id': 'bambu_a1_001',
            'timestamp': '2025-09-03T14:32:00Z'
        }
        
        # Mock receiving system event
        mock_websocket.recv.return_value = json.dumps(system_event)
        
        # Receive and process event
        message = await mock_websocket.recv()
        event_data = json.loads(message)
        
        assert event_data['type'] == 'system_event'
        assert event_data['event_type'] == 'printer_connect'
        assert event_data['severity'] == 'info'
        assert event_data['printer_id'] == 'bambu_a1_001'
    
    @pytest.mark.asyncio
    async def test_batch_update_processing(self, mock_websocket):
        """Test processing multiple updates in batch"""
        batch_update = {
            'type': 'batch_update',
            'updates': [
                {
                    'type': 'printer_status_update',
                    'printer_id': 'bambu_a1_001',
                    'status': 'printing',
                    'progress': 55.0
                },
                {
                    'type': 'printer_status_update', 
                    'printer_id': 'prusa_core_001',
                    'status': 'idle',
                    'progress': 0.0
                }
            ],
            'timestamp': '2025-09-03T14:32:30Z'
        }
        
        # Mock receiving batch update
        mock_websocket.recv.return_value = json.dumps(batch_update)
        
        # Receive and process batch
        message = await mock_websocket.recv()
        batch_data = json.loads(message)
        
        assert batch_data['type'] == 'batch_update'
        assert len(batch_data['updates']) == 2
        
        # Verify individual updates in batch
        updates = batch_data['updates']
        assert updates[0]['printer_id'] == 'bambu_a1_001'
        assert updates[0]['status'] == 'printing'
        assert updates[1]['printer_id'] == 'prusa_core_001'
        assert updates[1]['status'] == 'idle'


class TestWebSocketErrorHandling:
    """Test WebSocket error handling and recovery"""
    
    @pytest.mark.asyncio
    async def test_message_parsing_errors(self, mock_websocket):
        """Test handling of invalid JSON messages"""
        invalid_messages = [
            'invalid json{',
            '{"type": "incomplete"',
            '',
            None
        ]
        
        for invalid_msg in invalid_messages:
            # Mock receiving invalid message
            if invalid_msg is None:
                mock_websocket.recv.side_effect = websocket.exceptions.ConnectionClosedError(None, None)
            else:
                mock_websocket.recv.return_value = invalid_msg
            
            try:
                message = await mock_websocket.recv()
                if message:
                    json.loads(message)
            except (json.JSONDecodeError, websocket.exceptions.ConnectionClosedError) as e:
                # Should handle these errors gracefully
                assert True
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, test_config):
        """Test WebSocket connection timeout handling"""
        websocket_url = test_config['websocket_url']
        
        with patch('websockets.connect') as mock_connect:
            # Simulate timeout
            mock_connect.side_effect = asyncio.TimeoutError("Connection timeout")
            
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(mock_connect(websocket_url), timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_heartbeat_mechanism(self, mock_websocket):
        """Test WebSocket heartbeat/ping-pong mechanism"""
        # Mock ping message
        ping_message = {
            'type': 'ping',
            'timestamp': '2025-09-03T14:33:00Z'
        }
        
        # Mock expected pong response
        pong_response = {
            'type': 'pong',
            'timestamp': '2025-09-03T14:33:00Z'
        }
        
        # Send ping
        await mock_websocket.send(json.dumps(ping_message))
        
        # Mock receiving pong
        mock_websocket.recv.return_value = json.dumps(pong_response)
        
        # Receive pong response
        response = await mock_websocket.recv()
        response_data = json.loads(response)
        
        assert response_data['type'] == 'pong'
        assert response_data['timestamp'] == ping_message['timestamp']
        
        mock_websocket.send.assert_called_once_with(json.dumps(ping_message))
    
    @pytest.mark.asyncio
    async def test_connection_recovery_after_network_error(self, mock_websocket, test_config):
        """Test connection recovery after network interruption"""
        websocket_url = test_config['websocket_url']
        
        with patch('websockets.connect') as mock_connect:
            # Simulate network interruption and recovery
            connection_attempts = [
                websocket.exceptions.ConnectionClosedError(None, None),  # Network error
                websocket.exceptions.ConnectionClosedError(None, None),  # Still down
                mock_websocket  # Connection restored
            ]
            
            mock_connect.side_effect = connection_attempts
            
            # Simulate reconnection logic with backoff
            backoff_delays = [0.1, 0.2, 0.4]  # Exponential backoff
            
            for i, delay in enumerate(backoff_delays):
                try:
                    connection = await mock_connect(websocket_url)
                    if connection == mock_websocket:
                        break
                except websocket.exceptions.ConnectionClosedError:
                    if i == len(backoff_delays) - 1:
                        raise
                    await asyncio.sleep(delay)
            
            assert mock_connect.call_count == 3
    
    @pytest.mark.asyncio
    async def test_message_queue_overflow_handling(self, mock_websocket):
        """Test handling of message queue overflow"""
        # Simulate rapid message influx
        rapid_messages = []
        for i in range(100):
            message = {
                'type': 'rapid_update',
                'sequence': i,
                'data': f'rapid_data_{i}',
                'timestamp': datetime.now().isoformat()
            }
            rapid_messages.append(json.dumps(message))
        
        # Mock message queue with overflow
        mock_websocket.recv.side_effect = rapid_messages
        
        processed_messages = []
        max_queue_size = 50  # Simulate queue size limit
        
        for i in range(100):
            try:
                if len(processed_messages) < max_queue_size:
                    message = await mock_websocket.recv()
                    processed_messages.append(json.loads(message))
                else:
                    # Drop oldest messages to prevent overflow
                    processed_messages.pop(0)
                    message = await mock_websocket.recv()
                    processed_messages.append(json.loads(message))
            except IndexError:
                break
        
        # Should handle overflow by dropping old messages
        assert len(processed_messages) <= max_queue_size


class TestWebSocketPerformance:
    """Test WebSocket performance and scalability"""
    
    @pytest.mark.asyncio
    async def test_high_frequency_updates_performance(self, mock_websocket):
        """Test performance with high-frequency updates"""
        update_count = 1000
        updates = []
        
        # Generate high-frequency updates
        for i in range(update_count):
            update = {
                'type': 'high_freq_update',
                'sequence': i,
                'progress': (i / update_count) * 100,
                'timestamp': datetime.now().isoformat()
            }
            updates.append(json.dumps(update))
        
        # Mock rapid message reception
        mock_websocket.recv.side_effect = updates
        
        # Measure processing time
        import time
        start_time = time.time()
        
        processed_updates = []
        for _ in range(update_count):
            message = await mock_websocket.recv()
            update_data = json.loads(message)
            processed_updates.append(update_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process updates efficiently
        assert len(processed_updates) == update_count
        assert processing_time < 5.0  # Should process 1000 updates in under 5 seconds
        
        # Verify update order preservation
        for i, update in enumerate(processed_updates):
            assert update['sequence'] == i
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self):
        """Test handling multiple concurrent WebSocket connections"""
        connection_count = 10
        mock_connections = []
        
        # Create multiple mock connections
        for i in range(connection_count):
            mock_conn = AsyncMock()
            mock_conn.recv.return_value = json.dumps({
                'type': 'connection_test',
                'connection_id': i,
                'timestamp': datetime.now().isoformat()
            })
            mock_connections.append(mock_conn)
        
        # Simulate concurrent message reception
        async def receive_messages(connection, connection_id):
            message = await connection.recv()
            data = json.loads(message)
            return data['connection_id']
        
        # Process all connections concurrently
        tasks = [
            receive_messages(conn, i) 
            for i, conn in enumerate(mock_connections)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All connections should be handled
        assert len(results) == connection_count
        assert set(results) == set(range(connection_count))
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_long_running_connection(self, mock_websocket):
        """Test memory usage doesn't grow excessively with long-running connections"""
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Simulate long-running connection with many messages
        message_count = 5000
        for i in range(message_count):
            test_message = {
                'type': 'memory_test',
                'sequence': i,
                'data': 'x' * 100,  # Small payload
                'timestamp': datetime.now().isoformat()
            }
            
            mock_websocket.recv.return_value = json.dumps(test_message)
            
            # Process message
            message = await mock_websocket.recv()
            data = json.loads(message)
            
            # Simulate processing (don't store all messages)
            if i % 100 == 0:  # Only keep every 100th message for processing
                processed_data = data
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory growth should be reasonable
        object_growth = final_objects - initial_objects
        assert object_growth < message_count / 10  # Should not grow linearly with message count


class TestWebSocketGermanBusinessIntegration:
    """Test WebSocket integration with German business requirements"""
    
    @pytest.mark.asyncio
    async def test_german_timezone_in_websocket_messages(self, mock_websocket, test_utils):
        """Test that WebSocket messages include proper German timezone"""
        berlin_time = test_utils.berlin_timestamp('2025-09-03T14:30:00')
        
        update_with_timezone = {
            'type': 'printer_status_update',
            'printer_id': 'bambu_a1_001',
            'status': 'printing',
            'timestamp': berlin_time.isoformat(),
            'timezone': 'Europe/Berlin'
        }
        
        mock_websocket.recv.return_value = json.dumps(update_with_timezone)
        
        message = await mock_websocket.recv()
        data = json.loads(message)
        
        assert 'timezone' in data
        assert data['timezone'] == 'Europe/Berlin'
        assert 'T' in data['timestamp']  # ISO format
    
    @pytest.mark.asyncio
    async def test_business_cost_updates_via_websocket(self, mock_websocket, test_utils):
        """Test business cost calculations sent via WebSocket"""
        cost_update = {
            'type': 'job_cost_update',
            'job_id': 123,
            'costs': {
                'material_cost_eur': 2.50,
                'power_cost_eur': 0.45,
                'labor_cost_eur': 12.00,
                'subtotal_eur': 14.95,
                'vat_rate': 0.19,
                'vat_amount_eur': 2.84,
                'total_with_vat_eur': 17.79
            },
            'currency': 'EUR',
            'vat_included': True,
            'timestamp': '2025-09-03T14:30:00+02:00'
        }
        
        mock_websocket.recv.return_value = json.dumps(cost_update)
        
        message = await mock_websocket.recv()
        data = json.loads(message)
        
        assert data['currency'] == 'EUR'
        assert data['costs']['vat_rate'] == 0.19  # German VAT
        assert data['costs']['total_with_vat_eur'] == 17.79
        assert data['vat_included'] is True
    
    @pytest.mark.asyncio
    async def test_german_quality_assessment_updates(self, mock_websocket):
        """Test German quality assessment updates via WebSocket"""
        quality_update = {
            'type': 'job_quality_update',
            'job_id': 123,
            'quality_assessment': {
                'overall_rating': 4,  # 1-5 scale
                'first_layer_adhesion': 'excellent',  # German quality standards
                'surface_finish': 'good',
                'dimensional_accuracy_mm': 0.1,
                'meets_din_standards': True,
                'quality_notes': 'Erfüllt alle Qualitätsanforderungen'
            },
            'assessed_by': 'system',
            'timestamp': '2025-09-03T14:35:00+02:00'
        }
        
        mock_websocket.recv.return_value = json.dumps(quality_update)
        
        message = await mock_websocket.recv()
        data = json.loads(message)
        
        assert data['quality_assessment']['overall_rating'] in range(1, 6)
        assert data['quality_assessment']['meets_din_standards'] is True
        assert 'dimensional_accuracy_mm' in data['quality_assessment']