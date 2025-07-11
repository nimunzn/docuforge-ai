# DocuForge AI - OpenTelemetry Observability

This directory contains the complete OpenTelemetry observability setup for DocuForge AI, providing enterprise-grade monitoring, tracing, and metrics for the multi-agent AI system.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ with requirements.txt dependencies installed

### Starting the Observability Stack

```bash
# Start all observability services
cd .opentelemetry
./scripts/start-observability.sh
```

### Stopping the Observability Stack

```bash
# Stop all services
./scripts/stop-observability.sh
```

## 📊 Monitoring Dashboards

Once started, access these monitoring tools:

| Service | URL | Purpose | Default Login |
|---------|-----|---------|---------------|
| **Jaeger** | http://localhost:16686 | Distributed tracing | No login required |
| **Prometheus** | http://localhost:9090 | Metrics collection | No login required |
| **Grafana** | http://localhost:3000 | Dashboards & visualization | admin/admin |

## 🔍 What's Being Monitored

### LLM Operations
- **Request rate** per provider (OpenAI, Claude, Google)
- **Response latency** with percentiles (p50, p95, p99)
- **Token usage** and costs tracking
- **Error rates** and failure patterns
- **Model performance** comparisons

### Agent Activities
- **Agent execution** traces (Orchestrator, Planner, Writer, Reviewer)
- **Activity duration** and performance
- **Agent handoff** patterns and timing
- **Error tracking** per agent type

### System Health
- **HTTP request** rates and latencies
- **WebSocket connections** and message throughput
- **Database operations** (SQLAlchemy instrumentation)
- **Memory and CPU** usage patterns

### Document Generation
- **Document creation** success rates
- **Content generation** performance
- **User interaction** patterns
- **Preview update** frequencies

## 🔧 Configuration

### Environment Variables

The following environment variables can be used to customize the observability setup:

```bash
# OTEL Collector endpoint (default: http://localhost:4317)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Service identification
export OTEL_SERVICE_NAME=docuforge-ai
export OTEL_SERVICE_VERSION=1.0.0

# Sampling configuration (default: 1.0 = 100% sampling)
export OTEL_TRACES_SAMPLER=always_on
```

### Custom Metrics

The application exposes these custom metrics:

- `llm_requests_total` - Counter of LLM API calls
- `llm_request_duration_seconds` - Histogram of request durations
- `llm_tokens_total` - Counter of tokens consumed
- `agent_activities_total` - Counter of agent activities
- `document_generation_total` - Counter of documents generated
- `websocket_connections_active` - Gauge of active WebSocket connections

### Tracing Instrumentation

Automatic instrumentation is enabled for:

- **FastAPI** - HTTP requests and responses
- **SQLAlchemy** - Database operations
- **HTTP requests** - Outbound API calls
- **Custom agents** - All agent activities
- **WebSocket** - Connection and message events

## 📈 Understanding the Data

### Jaeger Traces

View distributed traces to understand:
- Complete request flows from user input to document generation
- Agent handoff patterns and timing
- LLM API call sequences and performance
- Error propagation and failure points

### Prometheus Metrics

Query metrics to monitor:
- System performance over time
- Resource usage patterns
- Error rates and SLA compliance
- Cost tracking (token usage)

### Grafana Dashboards

Pre-built dashboards show:
- **System Overview** - High-level health metrics
- **LLM Performance** - API call performance and costs
- **Agent Activities** - Agent execution patterns
- **User Experience** - Response times and success rates

## 🎯 Key Performance Indicators (KPIs)

Monitor these critical metrics:

1. **Response Time**: p95 latency < 5 seconds
2. **Success Rate**: > 99% successful document generations
3. **LLM Availability**: < 1% error rate for API calls
4. **Agent Performance**: Average agent execution < 2 seconds
5. **User Experience**: WebSocket connection success > 99%

## 🔧 Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check Docker status
docker info

# View container logs
docker-compose logs -f
```

**OTEL data not appearing:**
```bash
# Check if telemetry is initialized
curl http://localhost:4317/v1/traces

# Verify environment variables
env | grep OTEL
```

**Performance issues:**
```bash
# Reduce sampling rate
export OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling
```

### Log Analysis

View real-time logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f jaeger
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

## 🔐 Security Considerations

- **Default setup** is for development only
- **Production deployment** should use:
  - Authentication for Grafana
  - TLS encryption for all endpoints
  - Network isolation for internal services
  - Secure storage for metrics data

## 📚 Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Tracing Guide](https://www.jaegertracing.io/docs/)
- [Prometheus Query Guide](https://prometheus.io/docs/prometheus/latest/querying/)
- [Grafana Dashboard Guide](https://grafana.com/docs/grafana/latest/dashboards/)

## 🤝 Support

For questions or issues with observability setup:

1. Check the troubleshooting section above
2. Review container logs for errors
3. Verify Docker and networking configuration
4. Ensure all required ports are available (3000, 4317, 9090, 16686)

---

*This observability setup provides comprehensive monitoring for DocuForge AI's multi-agent document generation system.*