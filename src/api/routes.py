from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Header, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import logging

from ..core.security import verify_api_key
from ..core.config import settings
from ..websocket.manager import manager

logger = logging.getLogger(__name__)

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
async def test_page():
    """Test page for WebSocket client"""
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>WebSocket Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                input { padding: 8px; margin: 5px; }
                button { padding: 8px 15px; margin: 5px; cursor: pointer; }
                .error { color: red; }
                .success { color: green; }
                #messages { list-style: none; padding: 0; }
                #messages li { padding: 5px; margin: 5px 0; background: #f0f0f0; }
            </style>
        </head>
        <body>
            <h1>WebSocket Test Client (API Key Required)</h1>
            <form action="" onsubmit="sendMessage(event)">
                <div>
                    <input type="text" id="apiKey" placeholder="API Key" style="width: 300px;" />
                </div>
                <div>
                    <input type="text" id="clientId" placeholder="Client ID" value="user123" />
                    <button type="button" onclick="connect()">Connect</button>
                    <button type="button" onclick="disconnect()">Disconnect</button>
                </div>
                <hr>
                <input type="text" id="messageText" autocomplete="off" placeholder="Type message..." style="width: 400px;"/>
                <button>Send</button>
            </form>
            <ul id='messages'></ul>
            <script>
                var ws = null;

                function connect() {
                    const clientId = document.getElementById("clientId").value;
                    const apiKey = document.getElementById("apiKey").value;

                    if (!apiKey) {
                        addMessage('Please enter API key', 'error');
                        return;
                    }

                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}?api_key=${encodeURIComponent(apiKey)}`;

                    ws = new WebSocket(wsUrl);

                    ws.onmessage = function(event) {
                        addMessage(event.data);
                    };

                    ws.onopen = function() {
                        addMessage('Connected!', 'success');
                    };

                    ws.onclose = function(event) {
                        if (event.code === 1008) {
                            addMessage('Disconnected: Invalid API key', 'error');
                        } else {
                            addMessage('Disconnected!', 'error');
                        }
                    };

                    ws.onerror = function(error) {
                        addMessage('Connection error', 'error');
                    };
                }

                function addMessage(text, className) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    message.appendChild(document.createTextNode(text));
                    if (className) {
                        message.className = className;
                    }
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;
                }

                function disconnect() {
                    if (ws) {
                        ws.close();
                        ws = null;
                    }
                }

                function sendMessage(event) {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        var input = document.getElementById("messageText");
                        ws.send(input.value);
                        input.value = '';
                    } else {
                        alert('Please connect first!');
                    }
                    event.preventDefault();
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)
