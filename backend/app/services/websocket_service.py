from fastapi import WebSocket
from typing import Dict, List
import json
from app.models.schemas import WebSocketMessage
from app.telemetry import trace_function, telemetry


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    @trace_function("websocket_connect")
    async def connect(self, websocket: WebSocket, document_id: int):
        print(f"🔗 WebSocketManager.connect() called for document {document_id}")
        await websocket.accept()
        print(f"🤝 WebSocket accepted for document {document_id}")
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
            print(f"📝 Created new connection list for document {document_id}")
        self.active_connections[document_id].append(websocket)
        print(f"✅ WebSocket connected for document {document_id}. Total connections: {len(self.active_connections[document_id])}")
        print(f"🗂️ All active connections: {list(self.active_connections.keys())}")
        
        # Record connection metrics
        telemetry.record_websocket_connection(1, document_id)

    @trace_function("websocket_disconnect")
    def disconnect(self, websocket: WebSocket, document_id: int):
        if document_id in self.active_connections:
            if websocket in self.active_connections[document_id]:
                self.active_connections[document_id].remove(websocket)
                print(f"❌ WebSocket disconnected for document {document_id}. Remaining connections: {len(self.active_connections[document_id])}")
                # Record disconnection metrics
                telemetry.record_websocket_connection(-1, document_id)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
                print(f"🔴 No more connections for document {document_id}")
        else:
            print(f"⚠️  Attempted to disconnect non-existent connection for document {document_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    @trace_function("websocket_broadcast")
    async def broadcast_to_document(self, document_id: int, message: WebSocketMessage):
        if document_id in self.active_connections:
            message_str = json.dumps(message.dict())
            print(f"Broadcasting to document {document_id}: {len(self.active_connections[document_id])} connections")
            print(f"Message: {message_str[:200]}...")
            for connection in self.active_connections[document_id]:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    print(f"Failed to send WebSocket message: {e}")
        else:
            print(f"No WebSocket connections for document {document_id}")

    async def send_to_document(self, document_id: int, message: WebSocketMessage):
        await self.broadcast_to_document(document_id, message)