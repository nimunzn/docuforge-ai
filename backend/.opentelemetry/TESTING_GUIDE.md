# OpenTelemetry Stack Testing Guide

This guide will help you verify that each component of the observability stack is working correctly.

## 🧪 Testing Overview

We'll test in this order:
1. **OTEL Collector** - Verify it can receive and forward data
2. **Jaeger** - Confirm traces are being received
3. **Prometheus** - Check metrics collection
4. **Grafana** - Validate dashboards and data sources
5. **End-to-End** - Test with actual application

## 1. 🔄 OTEL Collector Health Check

### Check Collector Status
```bash
# Check if collector is accepting connections
curl -v http://localhost:4318/v1/traces

# Check collector metrics endpoint
curl http://localhost:8889/metrics | grep otelcol
```

**What to look for:**
- You should get a `405 Method Not Allowed` for the traces endpoint (this is normal - it expects POST)
- The metrics endpoint should return OTEL collector internal metrics

### Test OTLP Reception
```bash
# Send a test trace using curl
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [{
          "key": "service.name",
          "value": {"stringValue": "test-service"}
        }]
      },
      "scopeSpans": [{
        "spans": [{
          "traceId": "5B8EFFF798038103D269B633813FC60C",
          "spanId": "EEE19B7EC3C1B174",
          "name": "test-span",
          "startTimeUnixNano": "'$(date +%s)'000000000",
          "endTimeUnixNano": "'$(date +%s)'000000100"
        }]
      }]
    }]
  }'
```

**Expected result:** You should get a `200 OK` response

## 2. 🔍 Jaeger Testing

### Access Jaeger UI
1. Open http://localhost:16686
2. You should see the Jaeger UI load successfully

### What to Check:
1. **Service List**: Click on "Service" dropdown
   - After sending the test trace above, you should see "test-service"
   - Once your app runs, you'll see services like "docuforge-ai"

2. **Find Traces**: 
   - Select a service
   - Click "Find Traces"
   - You should see trace entries

3. **Trace Details**:
   - Click on any trace
   - You should see the span timeline
   - Check for span attributes and tags

### Key Areas in Jaeger:
- **System Architecture** tab - Shows service dependencies
- **Compare** tab - Compare trace performance
- **Deep Dependency** - Visualize service mesh

## 3. 📊 Prometheus Testing

### Access Prometheus UI
1. Open http://localhost:9090
2. You should see the Prometheus UI

### What to Check:

1. **Targets Health** (Status → Targets):
   - Look for "otel-collector" target
   - Status should be "UP"
   - Last scrape should be recent

2. **Test Queries** (Graph tab):
   ```promql
   # Check if collector is exposing metrics
   up{job="otel-collector"}
   
   # Once app is running, check for custom metrics:
   llm_requests_total
   agent_activities_total
   websocket_connections_active
   ```

3. **Key Metrics to Monitor**:
   - `otelcol_receiver_accepted_spans` - Spans received by collector
   - `otelcol_receiver_refused_spans` - Rejected spans (should be 0)
   - `otelcol_exporter_sent_spans` - Spans sent to Jaeger

## 4. 📈 Grafana Testing

### Access Grafana
1. Open http://localhost:3001
2. Login with `admin`/`admin`
3. Skip password change (or set a new one)

### What to Check:

1. **Data Sources** (Configuration → Data Sources):
   - "Prometheus" should be configured
   - Click "Test" - should show "Data source is working"

2. **Import Dashboard**:
   ```bash
   # The dashboard we created is at:
   /Users/nimoo/Documents/Code/docuforge-ai/backend/.opentelemetry/dashboards/docuforge-overview.json
   ```
   - Go to Dashboards → Import
   - Upload the JSON file or paste its contents
   - Select "Prometheus" as the data source

3. **Dashboard Panels** (once app is running):
   - LLM Request Rate
   - LLM Request Duration
   - Agent Activities
   - WebSocket Connections
   - Error Rates

## 5. 🚀 End-to-End Application Testing

### Start Your Backend
```bash
cd /Users/nimoo/Documents/Code/docuforge-ai/backend
python -m uvicorn app.main:app --reload
```

### Generate Test Traffic
1. Open your frontend application
2. Perform these actions:
   - Create a new document
   - Send a chat message
   - Request document generation
   - Open WebSocket connections

### Verify in Each Service:

#### In Jaeger:
- Look for service "docuforge-ai"
- Find traces for:
  - `POST /api/documents`
  - `agent.orchestrator.process_user_request`
  - `llm.openai.generate`
  - `websocket_connect`

#### In Prometheus:
Query these metrics:
```promql
# LLM requests by provider
sum(rate(llm_requests_total[5m])) by (provider)

# Agent activities by type
sum(rate(agent_activities_total[5m])) by (agent_type)

# WebSocket connections
websocket_connections_active

# HTTP request rate
sum(rate(http_server_duration_count[5m])) by (http_route)
```

#### In Grafana:
- All panels should show data
- No "No Data" errors
- Graphs should update in real-time

## 6. 🔧 Troubleshooting Common Issues

### No Data in Jaeger
```bash
# Check OTEL collector logs
docker logs otel-collector --tail 50

# Verify your app has OTEL endpoint configured
echo $OTEL_EXPORTER_OTLP_ENDPOINT  # Should be http://localhost:4317
```

### No Metrics in Prometheus
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify collector is exposing metrics
curl http://localhost:8889/metrics
```

### Application Not Sending Telemetry
```python
# In your Python app, check telemetry initialization
import os
os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4317'

# Run a test script
python -c "
from app.telemetry import telemetry
telemetry.initialize('test-app', '1.0.0')
print('Telemetry initialized:', telemetry.initialized)
"
```

## 7. 📋 Quick Validation Checklist

Run through this checklist to ensure everything works:

- [ ] OTEL Collector accepts traces on port 4318 (HTTP)
- [ ] OTEL Collector accepts traces on port 4317 (gRPC)
- [ ] Jaeger UI loads at http://localhost:16686
- [ ] Prometheus UI loads at http://localhost:9090
- [ ] Grafana UI loads at http://localhost:3001
- [ ] Test trace appears in Jaeger
- [ ] Prometheus shows otel-collector as UP
- [ ] Grafana can query Prometheus successfully
- [ ] Application sends traces when running
- [ ] Custom metrics appear in Prometheus
- [ ] Grafana dashboard shows real data

## 8. 🎯 Performance Testing

### Load Test with Traces
```python
# Save as test_telemetry.py
import asyncio
import time
from app.telemetry import telemetry, trace_function

telemetry.initialize("load-test", "1.0.0")

@trace_function("test_operation")
async def test_operation(i):
    await asyncio.sleep(0.1)
    return f"Operation {i} complete"

async def main():
    tasks = [test_operation(i) for i in range(100)]
    await asyncio.gather(*tasks)
    print("Load test complete - check Jaeger for traces")

asyncio.run(main())
```

Run this and verify:
- Jaeger shows 100 traces
- No dropped spans in collector metrics
- Prometheus shows increased activity

---

**Success Criteria**: If all items in the checklist pass, your observability stack is fully operational! 🎉