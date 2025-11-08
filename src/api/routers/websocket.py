"""WebSocket endpoints for real-time updates."""

from typing import Dict, Set
import json
import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from src.services.event_service import EventService


logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.printer_subscriptions: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to accept and register.
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected", total_connections=len(self.active_connections))
        
    def disconnect(self, websocket: WebSocket):
        """Unregister a WebSocket connection and clean up subscriptions.

        Args:
            websocket: WebSocket connection to disconnect and remove from all subscriptions.
        """
        self.active_connections.discard(websocket)
        # Remove from printer subscriptions
        for printer_id, connections in self.printer_subscriptions.items():
            connections.discard(websocket)
        logger.info("WebSocket client disconnected", total_connections=len(self.active_connections))
        
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.add(connection)
                
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
            
    async def send_to_printer_subscribers(self, printer_id: str, message: dict):
        """Send message to clients subscribed to specific printer."""
        connections = self.printer_subscriptions.get(printer_id, set())
        if not connections:
            return
            
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.add(connection)
                
        # Clean up disconnected clients
        for connection in disconnected:
            connections.discard(connection)
            
    def subscribe_to_printer(self, websocket: WebSocket, printer_id: str):
        """Subscribe websocket to printer updates."""
        if printer_id not in self.printer_subscriptions:
            self.printer_subscriptions[printer_id] = set()
        self.printer_subscriptions[printer_id].add(websocket)
        
    def unsubscribe_from_printer(self, websocket: WebSocket, printer_id: str):
        """Unsubscribe websocket from printer updates."""
        if printer_id in self.printer_subscriptions:
            self.printer_subscriptions[printer_id].discard(websocket)


manager = ConnectionManager()


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates."""
    event_service = websocket.app.state.event_service
    await _handle_websocket_connection(websocket, event_service)

async def _handle_websocket_connection(websocket: WebSocket, event_service: EventService):
    """Handle WebSocket connection lifecycle and message processing.

    Manages the full lifecycle of a WebSocket connection including accepting the connection,
    processing incoming client messages, and handling disconnection.

    Args:
        websocket: WebSocket connection to handle.
        event_service: Event service for publishing real-time updates.

    Raises:
        WebSocketDisconnect: When the client disconnects.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error("Error handling WebSocket message", error=str(e))
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": "Internal server error"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming client messages."""
    message_type = message.get("type")
    
    if message_type == "subscribe_printer":
        printer_id = message.get("printer_id")
        if printer_id:
            manager.subscribe_to_printer(websocket, printer_id)
            await websocket.send_text(json.dumps({
                "type": "subscribed",
                "printer_id": printer_id
            }))
            
    elif message_type == "unsubscribe_printer":
        printer_id = message.get("printer_id")
        if printer_id:
            manager.unsubscribe_from_printer(websocket, printer_id)
            await websocket.send_text(json.dumps({
                "type": "unsubscribed", 
                "printer_id": printer_id
            }))
            
    elif message_type == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))
        
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


# Event handlers for broadcasting updates
async def broadcast_printer_status(printer_id: UUID, status_data: dict):
    """Broadcast printer status update."""
    await manager.send_to_printer_subscribers(str(printer_id), {
        "type": "printer_status",
        "printer_id": str(printer_id),
        "data": status_data
    })


async def broadcast_job_update(job_id: UUID, job_data: dict):
    """Broadcast job progress update."""
    await manager.broadcast({
        "type": "job_update",
        "job_id": str(job_id),
        "data": job_data
    })


async def broadcast_system_event(event_type: str, event_data: dict):
    """Broadcast system event."""
    await manager.broadcast({
        "type": "system_event",
        "event_type": event_type,
        "data": event_data
    })


# Make connection manager available for other modules
def get_connection_manager() -> ConnectionManager:
    return manager