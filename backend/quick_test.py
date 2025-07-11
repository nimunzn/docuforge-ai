#!/usr/bin/env python3
"""
Quick test to send traces directly to Jaeger (bypassing problematic collector)
"""
import os
import asyncio

# Set Jaeger direct endpoint
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:14268"

from app.telemetry import telemetry, trace_function

# Initialize with direct Jaeger connection
telemetry.initialize("docuforge-ai-direct", "1.0.0")

@trace_function("direct_api_test")
async def test_api_request():
    """Simulate API request processing"""
    print("🌐 Processing API request...")
    await asyncio.sleep(0.2)
    return "API response"

@trace_function("direct_websocket_test") 
async def test_websocket():
    """Simulate WebSocket connection"""
    print("🔌 WebSocket connecting...")
    await asyncio.sleep(0.1)
    telemetry.record_websocket_connection(1, document_id=999)
    return "WebSocket connected"

async def main():
    print("🚀 Sending traces directly to Jaeger...")
    await test_api_request()
    await test_websocket()
    print("✅ Check Jaeger for 'docuforge-ai-direct' service!")

if __name__ == "__main__":
    asyncio.run(main())