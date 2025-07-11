#!/usr/bin/env python3
"""
Debug script to test OpenTelemetry with proper environment setup
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.telemetry")

# Set the endpoint explicitly
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317"

print("🔧 Environment Variables:")
print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')}")
print(f"OTEL_SERVICE_NAME: {os.environ.get('OTEL_SERVICE_NAME')}")
print(f"OTEL_SERVICE_VERSION: {os.environ.get('OTEL_SERVICE_VERSION')}")

# Now import and test telemetry
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.telemetry import telemetry
    print(f"\n🔭 Telemetry Status:")
    print(f"Initialized: {telemetry.initialized}")
    
    # Force initialization
    telemetry.initialize("docuforge-ai-debug", "1.0.0")
    print(f"After init: {telemetry.initialized}")
    
    if telemetry.initialized:
        print("✅ Telemetry is working!")
        
        # Test sending a trace
        import asyncio
        from app.telemetry import trace_function
        
        @trace_function("debug_test")
        async def test_trace():
            print("📤 Sending test trace...")
            await asyncio.sleep(0.1)
            return "Test complete"
        
        asyncio.run(test_trace())
        print("✅ Test trace sent! Check Jaeger for 'docuforge-ai-debug' service")
    else:
        print("❌ Telemetry initialization failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()