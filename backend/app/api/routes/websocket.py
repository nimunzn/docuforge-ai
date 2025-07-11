from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
import json
from app.core.database import get_db
from app.models.schemas import WebSocketMessage
from app.services.websocket_service import WebSocketManager

router = APIRouter()
manager = WebSocketManager()


@router.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: int):
    print(f"🎯 WebSocket connection attempt for document {document_id}")
    print(f"📍 WebSocket client: {websocket.client}")
    await manager.connect(websocket, document_id)
    print(f"✅ WebSocket connected and registered for document {document_id}")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "document_update":
                await manager.broadcast_to_document(
                    document_id, 
                    WebSocketMessage(
                        type="document_update",
                        data=message.get("data", {})
                    )
                )
            elif message.get("type") == "typing":
                await manager.broadcast_to_document(
                    document_id,
                    WebSocketMessage(
                        type="typing",
                        data={"user": message.get("user", "anonymous")}
                    )
                )
            elif message.get("type") == "chat_message":
                await manager.broadcast_to_document(
                    document_id,
                    WebSocketMessage(
                        type="chat_message",
                        data=message.get("data", {})
                    )
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, document_id)