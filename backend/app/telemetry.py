"""
OpenTelemetry Telemetry Service for DocuForge AI
Provides centralized observability for the multi-agent AI system
"""
import os
import time
from typing import Dict, Any, Optional
from functools import wraps

# Try to import OpenTelemetry, gracefully handle if not available
try:
    from opentelemetry import trace, metrics
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.semconv.resource import ResourceAttributes
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("⚠️  OpenTelemetry not available. Install with: pip install -r requirements.txt")
    
    # Mock classes for when OpenTelemetry isn't available
    class MockTracer:
        def start_as_current_span(self, name):
            return MockSpan()
    
    class MockSpan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_attribute(self, key, value):
            pass
    
    class MockMeter:
        def create_counter(self, *args, **kwargs):
            return MockMetric()
        def create_histogram(self, *args, **kwargs):
            return MockMetric()
        def create_up_down_counter(self, *args, **kwargs):
            return MockMetric()
    
    class MockMetric:
        def add(self, *args, **kwargs):
            pass
        def record(self, *args, **kwargs):
            pass


class TelemetryService:
    """Centralized telemetry service for DocuForge AI"""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self.initialized = False
        
        # Metrics
        self.llm_request_counter = None
        self.llm_request_duration = None
        self.llm_token_counter = None
        self.agent_activity_counter = None
        self.document_generation_counter = None
        self.websocket_connections_gauge = None
        
    def initialize(self, service_name: str = "docuforge-ai", service_version: str = "1.0.0"):
        """Initialize OpenTelemetry with OTLP exporters"""
        if self.initialized:
            return
            
        if not OTEL_AVAILABLE:
            print("⚠️  OpenTelemetry not available, using mock telemetry")
            self.tracer = MockTracer()
            self.meter = MockMeter()
            self.initialized = True
            return
            
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            ResourceAttributes.SERVICE_INSTANCE_ID: os.environ.get("HOSTNAME", "local"),
        })
        
        # Configure tracing
        trace_provider = TracerProvider(resource=resource)
        
        # OTLP exporter endpoint
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        
        # Trace exporter
        trace_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True  # For development
        )
        
        span_processor = BatchSpanProcessor(trace_exporter)
        trace_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(trace_provider)
        
        self.tracer = trace.get_tracer(__name__)
        
        # Configure metrics
        metric_exporter = OTLPMetricExporter(
            endpoint=otlp_endpoint,
            insecure=True
        )
        
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=5000  # Export every 5 seconds
        )
        
        metrics_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        
        metrics.set_meter_provider(metrics_provider)
        self.meter = metrics.get_meter(__name__)
        
        # Initialize metrics
        self._initialize_metrics()
        
        self.initialized = True
        print(f"🔭 OpenTelemetry initialized for {service_name} with endpoint: {otlp_endpoint}")
    
    def _initialize_metrics(self):
        """Initialize custom metrics for DocuForge AI"""
        
        if not self.meter:
            return
            
        # LLM Request metrics
        self.llm_request_counter = self.meter.create_counter(
            "llm_requests_total",
            description="Total number of LLM requests",
            unit="1"
        )
        
        self.llm_request_duration = self.meter.create_histogram(
            "llm_request_duration_seconds",
            description="Duration of LLM requests in seconds",
            unit="s"
        )
        
        self.llm_token_counter = self.meter.create_counter(
            "llm_tokens_total",
            description="Total number of tokens used",
            unit="1"
        )
        
        # Agent Activity metrics
        self.agent_activity_counter = self.meter.create_counter(
            "agent_activities_total",
            description="Total number of agent activities",
            unit="1"
        )
        
        # Document Generation metrics
        self.document_generation_counter = self.meter.create_counter(
            "document_generation_total",
            description="Total number of document generations",
            unit="1"
        )
        
        # WebSocket Connection metrics
        self.websocket_connections_gauge = self.meter.create_up_down_counter(
            "websocket_connections_active",
            description="Number of active WebSocket connections",
            unit="1"
        )
    
    def record_llm_request(self, provider: str, model: str, duration: float, 
                          tokens_used: int = 0, status: str = "success"):
        """Record LLM request metrics"""
        if not self.initialized or not self.llm_request_counter:
            return
            
        attributes = {
            "provider": provider,
            "model": model,
            "status": status
        }
        
        self.llm_request_counter.add(1, attributes)
        self.llm_request_duration.record(duration, attributes)
        
        if tokens_used > 0:
            self.llm_token_counter.add(tokens_used, attributes)
    
    def record_agent_activity(self, agent_type: str, activity_type: str, status: str = "success"):
        """Record agent activity metrics"""
        if not self.initialized or not self.agent_activity_counter:
            return
            
        attributes = {
            "agent_type": agent_type,
            "activity_type": activity_type,
            "status": status
        }
        
        self.agent_activity_counter.add(1, attributes)
    
    def record_document_generation(self, document_type: str, status: str = "success"):
        """Record document generation metrics"""
        if not self.initialized or not self.document_generation_counter:
            return
            
        attributes = {
            "document_type": document_type,
            "status": status
        }
        
        self.document_generation_counter.add(1, attributes)
    
    def record_websocket_connection(self, change: int, document_id: Optional[int] = None):
        """Record WebSocket connection changes"""
        if not self.initialized or not self.websocket_connections_gauge:
            return
            
        attributes = {}
        if document_id:
            attributes["document_id"] = str(document_id)
            
        self.websocket_connections_gauge.add(change, attributes)


# Global telemetry instance
telemetry = TelemetryService()


def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to trace function calls"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not telemetry.initialized:
                return await func(*args, **kwargs)
                
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with telemetry.tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.status", "error")
                    span.set_attribute("function.error", str(e))
                    raise
                finally:
                    duration = time.time() - start_time
                    span.set_attribute("function.duration", duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not telemetry.initialized:
                return func(*args, **kwargs)
                
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with telemetry.tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.status", "error")
                    span.set_attribute("function.error", str(e))
                    raise
                finally:
                    duration = time.time() - start_time
                    span.set_attribute("function.duration", duration)
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def trace_llm(provider: str, model: str, operation: str = "generate"):
    """Decorator to trace LLM calls with enhanced metrics"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not telemetry.initialized:
                return await func(*args, **kwargs)
                
            span_name = f"llm.{provider}.{operation}"
            
            with telemetry.tracer.start_as_current_span(span_name) as span:
                # Add LLM-specific attributes
                span.set_attribute("llm.provider", provider)
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.operation", operation)
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record successful metrics
                    duration = time.time() - start_time
                    telemetry.record_llm_request(provider, model, duration, status="success")
                    
                    span.set_attribute("llm.status", "success")
                    span.set_attribute("llm.duration", duration)
                    
                    # Try to extract token information if available
                    if hasattr(result, 'usage') and result.usage:
                        total_tokens = getattr(result.usage, 'total_tokens', 0)
                        if total_tokens > 0:
                            telemetry.record_llm_request(provider, model, duration, total_tokens, "success")
                            span.set_attribute("llm.tokens.total", total_tokens)
                    
                    return result
                    
                except Exception as e:
                    # Record error metrics
                    duration = time.time() - start_time
                    telemetry.record_llm_request(provider, model, duration, status="error")
                    
                    span.set_attribute("llm.status", "error")
                    span.set_attribute("llm.error", str(e))
                    span.set_attribute("llm.duration", duration)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not telemetry.initialized:
                return func(*args, **kwargs)
                
            span_name = f"llm.{provider}.{operation}"
            
            with telemetry.tracer.start_as_current_span(span_name) as span:
                # Add LLM-specific attributes
                span.set_attribute("llm.provider", provider)
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.operation", operation)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Record successful metrics
                    duration = time.time() - start_time
                    telemetry.record_llm_request(provider, model, duration, status="success")
                    
                    span.set_attribute("llm.status", "success")
                    span.set_attribute("llm.duration", duration)
                    
                    return result
                    
                except Exception as e:
                    # Record error metrics
                    duration = time.time() - start_time
                    telemetry.record_llm_request(provider, model, duration, status="error")
                    
                    span.set_attribute("llm.status", "error")
                    span.set_attribute("llm.error", str(e))
                    span.set_attribute("llm.duration", duration)
                    raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def trace_agent(agent_type: str, activity_type: str = "process"):
    """Decorator to trace agent activities"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not telemetry.initialized:
                return await func(*args, **kwargs)
                
            span_name = f"agent.{agent_type}.{activity_type}"
            
            with telemetry.tracer.start_as_current_span(span_name) as span:
                # Add agent-specific attributes
                span.set_attribute("agent.type", agent_type)
                span.set_attribute("agent.activity", activity_type)
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record successful metrics
                    telemetry.record_agent_activity(agent_type, activity_type, "success")
                    
                    span.set_attribute("agent.status", "success")
                    span.set_attribute("agent.duration", time.time() - start_time)
                    
                    return result
                    
                except Exception as e:
                    # Record error metrics
                    telemetry.record_agent_activity(agent_type, activity_type, "error")
                    
                    span.set_attribute("agent.status", "error")
                    span.set_attribute("agent.error", str(e))
                    span.set_attribute("agent.duration", time.time() - start_time)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not telemetry.initialized:
                return func(*args, **kwargs)
                
            span_name = f"agent.{agent_type}.{activity_type}"
            
            with telemetry.tracer.start_as_current_span(span_name) as span:
                # Add agent-specific attributes
                span.set_attribute("agent.type", agent_type)
                span.set_attribute("agent.activity", activity_type)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Record successful metrics
                    telemetry.record_agent_activity(agent_type, activity_type, "success")
                    
                    span.set_attribute("agent.status", "success")
                    span.set_attribute("agent.duration", time.time() - start_time)
                    
                    return result
                    
                except Exception as e:
                    # Record error metrics
                    telemetry.record_agent_activity(agent_type, activity_type, "error")
                    
                    span.set_attribute("agent.status", "error")
                    span.set_attribute("agent.error", str(e))
                    span.set_attribute("agent.duration", time.time() - start_time)
                    raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator