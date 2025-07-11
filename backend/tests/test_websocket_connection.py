#!/usr/bin/env python3
"""
Test WebSocket connection manually
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection to document 5"""
    uri = "ws://localhost:8000/ws/5"
    
    try:
        logger.info(f"Connecting to {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket connected successfully")
            
            # Send a test message
            test_message = {
                "type": "test",
                "data": {"message": "Hello from test"}
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("📤 Test message sent")
            
            # Keep connection alive and listen for messages
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"📨 Received message: {message}")
            except asyncio.TimeoutError:
                logger.info("⏰ No messages received within timeout")
                
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())