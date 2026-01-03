from fastapi import WebSocket
from typing import List
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        try:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
        except ValueError:
            logger.warning("Client was already disconnected")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for connection in dead_connections:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                pass


manager = ConnectionManager()
