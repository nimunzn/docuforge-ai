#!/bin/bash

# Start DocuForge AI Backend Server with OpenTelemetry
echo "🚀 Starting DocuForge AI Backend with OpenTelemetry..."

# Set up environment
export PYTHONPATH=/Users/nimoo/Documents/Code/docuforge-ai/backend:$PYTHONPATH

# Load telemetry environment variables
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=docuforge-ai
export OTEL_SERVICE_VERSION=1.0.0
export OTEL_TRACES_SAMPLER=always_on

# Start the server
echo "🔧 Environment configured:"
echo "  OTEL_EXPORTER_OTLP_ENDPOINT: $OTEL_EXPORTER_OTLP_ENDPOINT"
echo "  OTEL_SERVICE_NAME: $OTEL_SERVICE_NAME"
echo "  PYTHONPATH: $PYTHONPATH"
echo ""

# Change to backend directory
cd /Users/nimoo/Documents/Code/docuforge-ai/backend

# Start uvicorn
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000