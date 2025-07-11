#!/bin/bash

# DocuForge AI - Stop Observability Stack
# This script stops the OpenTelemetry observability infrastructure

set -e

echo "🛑 Stopping DocuForge AI Observability Stack..."

# Navigate to the OpenTelemetry directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OTEL_DIR="$(dirname "$SCRIPT_DIR")"
cd "$OTEL_DIR"

# Stop and remove containers
echo "🔄 Stopping containers..."
docker-compose down

echo "✅ Observability stack stopped successfully!"
echo ""
echo "💡 To start again, run: ./scripts/start-observability.sh"
echo "🗑️  To remove all data (including metrics history), run: docker-compose down -v"