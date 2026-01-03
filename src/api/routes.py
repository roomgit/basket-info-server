from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Header, Query, Request
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging
from pathlib import Path

from ..core.security import verify_api_key
from ..core.config import settings
from ..websocket.manager import manager

logger = logging.getLogger(__name__)

# Setup templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent / "templates"))

router = APIRouter()


@router.get("/")
async def get(api_key: str = Header(None, alias="X-API-Key")):
    """Root endpoint with API information"""
    verify_api_key(api_key)
    return {
        "message": "WebSocket Server is running",
        "websocket_endpoint": "/ws/{client_id}?api_key=YOUR_API_KEY",
        "health_check": "/health"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections)
    }


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, api_key: Optional[str] = Query(None)):
    """WebSocket endpoint for real-time communication"""
    # Verify API key before accepting WebSocket connection
    if api_key != settings.API_KEY:
        logger.warning(f"WebSocket connection rejected: invalid API key from {client_id}")
        await websocket.close(code=1008, reason="Invalid API key")
        return

    await manager.connect(websocket)
    try:
        await manager.send_personal_message(f"Welcome! Your client ID: {client_id}", websocket)

        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from {client_id}: {data}")

            # Validate message length
            if len(data) > settings.MAX_MESSAGE_LENGTH:
                await manager.send_personal_message(
                    f"Error: Message too long (max {settings.MAX_MESSAGE_LENGTH} chars)",
                    websocket
                )
                continue

            await manager.send_personal_message(f"You sent: {data}", websocket)
            await manager.broadcast(f"Client {client_id} says: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left the chat")
    except Exception as e:
        logger.error(f"Error in websocket connection: {e}")
        manager.disconnect(websocket)


@router.get("/test")
async def test_page(request: Request):
    """Test page for WebSocket client"""
    return templates.TemplateResponse("test.html", {"request": request})
