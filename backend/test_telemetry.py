#!/usr/bin/env python3
"""
Test script to verify OpenTelemetry integration is working
Run this to send test traces and metrics to your observability stack
"""
import os
import sys
import time
import asyncio
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set OTEL endpoint before importing telemetry
os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4317'

from app.telemetry import telemetry, trace_function, trace_llm, trace_agent

# Initialize telemetry
print("🔧 Initializing telemetry...")
telemetry.initialize("telemetry-test", "1.0.0")
print(f"✅ Telemetry initialized: {telemetry.initialized}")

# Test functions with different trace types
@trace_function("test_basic_operation")
async def test_basic_operation():
    """Test basic function tracing"""
    print("  → Running basic operation")
    await asyncio.sleep(0.1)
    return "Basic operation complete"

@trace_llm("openai", "gpt-4", "test_generate")
async def test_llm_operation():
    """Test LLM tracing"""
    print("  → Simulating LLM call")
    start = time.time()
    await asyncio.sleep(0.5)  # Simulate API latency
    duration = time.time() - start
    
    # Record metrics
    telemetry.record_llm_request("openai", "gpt-4", duration, tokens_used=150, status="success")
    return "Generated text response"

@trace_agent("orchestrator", "test_process")
async def test_agent_operation():
    """Test agent tracing"""
    print("  → Simulating agent activity")
    await asyncio.sleep(0.2)
    
    # Record agent activity
    telemetry.record_agent_activity("orchestrator", "process_request", "success")
    return "Agent processing complete"

async def test_websocket_metrics():
    """Test WebSocket metrics"""
    print("  → Testing WebSocket metrics")
    
    # Simulate connections
    telemetry.record_websocket_connection(1, document_id=123)
    await asyncio.sleep(0.1)
    telemetry.record_websocket_connection(1, document_id=124)
    await asyncio.sleep(0.1)
    telemetry.record_websocket_connection(-1, document_id=123)
    
    return "WebSocket metrics recorded"

async def test_document_generation():
    """Test document generation metrics"""
    print("  → Testing document generation")
    
    telemetry.record_document_generation("proposal", "success")
    await asyncio.sleep(0.1)
    telemetry.record_document_generation("report", "success")
    await asyncio.sleep(0.1)
    telemetry.record_document_generation("template", "error")
    
    return "Document metrics recorded"

async def test_nested_traces():
    """Test nested trace spans"""
    print("  → Testing nested traces")
    
    @trace_function("outer_operation")
    async def outer_operation():
        result = await inner_operation()
        return f"Outer: {result}"
    
    @trace_function("inner_operation")
    async def inner_operation():
        await asyncio.sleep(0.1)
        return "Inner complete"
    
    return await outer_operation()

async def run_all_tests():
    """Run all telemetry tests"""
    print("\n🚀 Starting OpenTelemetry Tests\n")
    
    tests = [
        ("Basic Function Trace", test_basic_operation),
        ("LLM Operation Trace", test_llm_operation),
        ("Agent Activity Trace", test_agent_operation),
        ("WebSocket Metrics", test_websocket_metrics),
        ("Document Generation Metrics", test_document_generation),
        ("Nested Traces", test_nested_traces),
    ]
    
    for name, test_func in tests:
        print(f"\n📍 Test: {name}")
        try:
            result = await test_func()
            print(f"  ✅ Success: {result}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🎯 Test Summary:")
    print("="*50)
    print(f"Telemetry Service: {'✅ Active' if telemetry.initialized else '❌ Inactive'}")
    print(f"OTEL Endpoint: {os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'Not set')}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("\n📊 Check your observability stack:")
    print("  • Jaeger UI: http://localhost:16686")
    print("    → Look for service 'telemetry-test'")
    print("    → You should see 6 different trace operations")
    print("  • Prometheus: http://localhost:9090")
    print("    → Query: llm_requests_total")
    print("    → Query: agent_activities_total")
    print("    → Query: websocket_connections_active")
    print("  • Grafana: http://localhost:3001")
    print("    → Check the DocuForge AI dashboard")
    print("\n✨ Tests complete!")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())