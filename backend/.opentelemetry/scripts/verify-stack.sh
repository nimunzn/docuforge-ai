#!/bin/bash

# Verify OpenTelemetry Stack Health
echo "🔍 Verifying OpenTelemetry Stack Health..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    printf "Checking %-20s ... " "$name"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $response, expected $expected_code)"
        return 1
    fi
}

# Check each service
echo -e "\n📡 Service Health Checks:"
echo "------------------------"
check_service "OTEL Collector (HTTP)" "http://localhost:4318/v1/traces" "405"
check_service "OTEL Collector Metrics" "http://localhost:8889/metrics" "200"
check_service "Jaeger UI" "http://localhost:16686" "200"
check_service "Prometheus UI" "http://localhost:9090" "200"
check_service "Grafana UI" "http://localhost:3001" "200"

# Check Docker containers
echo -e "\n🐳 Docker Container Status:"
echo "---------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep otel

# Send a test trace
echo -e "\n📤 Sending Test Trace..."
echo "------------------------"
trace_response=$(curl -s -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [{
          "key": "service.name",
          "value": {"stringValue": "verify-test"}
        }]
      },
      "scopeSpans": [{
        "spans": [{
          "traceId": "'$(openssl rand -hex 16)'",
          "spanId": "'$(openssl rand -hex 8)'",
          "name": "health-check-span",
          "startTimeUnixNano": "'$(date +%s)'000000000",
          "endTimeUnixNano": "'$(date +%s)'000000100",
          "attributes": [{
            "key": "check.type",
            "value": {"stringValue": "health"}
          }]
        }]
      }]
    }]
  }' -w "\nHTTP Status: %{http_code}\n")

echo "$trace_response"

# Check Prometheus targets
echo -e "\n📊 Prometheus Targets:"
echo "---------------------"
targets=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"' 2>/dev/null)
if [ -n "$targets" ]; then
    echo "$targets"
else
    echo -e "${YELLOW}⚠️  Could not fetch Prometheus targets (jq might not be installed)${NC}"
fi

# Summary
echo -e "\n📋 Quick Access Links:"
echo "====================="
echo "• Jaeger UI:    http://localhost:16686"
echo "• Prometheus:   http://localhost:9090"
echo "• Grafana:      http://localhost:3001 (admin/admin)"
echo ""
echo "💡 Next Steps:"
echo "1. Check Jaeger for the 'verify-test' service"
echo "2. Run: cd ../.. && python test_telemetry.py"
echo "3. Start your application to see real telemetry data"