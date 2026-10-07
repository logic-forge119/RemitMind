import json
import logging
from typing import List, Set, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.auth import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Live Feeds"])

class AlertConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active listeners: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active listeners: {len(self.active_connections)}")

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcasts live risk alert to all connected analyst consoles."""
        if not self.active_connections:
            return
        
        payload = json.dumps({
            "type": "NEW_ALERT",
            "data": alert_data
        })
        
        disconnected = set()
        for conn in self.active_connections:
            try:
                await conn.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to send to websocket client: {e}")
                disconnected.add(conn)

        for conn in disconnected:
            self.disconnect(conn)

alert_manager = AlertConnectionManager()

@router.websocket("/ws/alerts")
@router.websocket("/api/v1/ws/alerts")
async def websocket_alerts_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    """
    Authenticated WebSocket feed streaming real-time remittance risk alerts to analysts.
    Requires valid JWT token with 'analyst' or 'admin' role passed as query param ?token=...
    """
    # 1. Validate JWT Token
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        return

    try:
        payload = decode_access_token(token)
        role = payload.get("role")
        if role not in ["analyst", "admin"]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient permissions")
            return
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=f"Invalid authentication token: {str(e)}")
        return

    # 2. Accept and manage connection
    await alert_manager.connect(websocket)
    try:
        # Send initial handshake acknowledgment
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "message": "Connected to RemitMind Live Alert Stream",
            "user": payload.get("sub"),
            "role": role
        }))
        
        # Keep connection alive; handle incoming pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        alert_manager.disconnect(websocket)

@router.get("/api/v1/ws/status")
def websocket_status():
    """Returns real-time connection status for WebSocket listeners."""
    return {
        "status": "online",
        "active_subscribers": len(alert_manager.active_connections),
        "channel": "/ws/alerts",
        "fallback": "polling"
    }
