#!/bin/bash

# DocuForge AI - Start Observability Stack
# This script starts the OpenTelemetry observability infrastructure

set -e

echo "🔭 Starting DocuForge AI Observability Stack..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to the OpenTelemetry directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OTEL_DIR="$(dirname "$SCRIPT_DIR")"
cd "$OTEL_DIR"

# Start the observability stack
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."

# Check Jaeger
if curl -s http://localhost:16686 >/dev/null; then
    echo "✅ Jaeger UI is ready at http://localhost:16686"
else
    echo "⚠️  Jaeger UI not responding at http://localhost:16686"
fi

# Check Prometheus
if curl -s http://localhost:9090 >/dev/null; then
    echo "✅ Prometheus is ready at http://localhost:9090"
else
    echo "⚠️  Prometheus not responding at http://localhost:9090"
fi

# Check Grafana
if curl -s http://localhost:3000 >/dev/null; then
    echo "✅ Grafana is ready at http://localhost:3000"
    echo "   Default login: admin/admin"
else
    echo "⚠️  Grafana not responding at http://localhost:3000"
fi

# Check OTEL Collector
if curl -s http://localhost:4317 >/dev/null 2>&1; then
    echo "✅ OTEL Collector is ready at http://localhost:4317"
else
    echo "⚠️  OTEL Collector not responding at http://localhost:4317"
fi

echo ""
echo "🎉 Observability stack is ready!"
echo ""
echo "📊 Access your monitoring tools:"
echo "   • Jaeger (Tracing):    http://localhost:16686"
echo "   • Prometheus (Metrics): http://localhost:9090"
echo "   • Grafana (Dashboards): http://localhost:3000 (admin/admin)"
echo ""
echo "🔧 To stop the stack, run: ./scripts/stop-observability.sh"
echo "📝 To view logs, run: docker-compose logs -f"