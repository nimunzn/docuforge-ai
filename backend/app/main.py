import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.routes import documents, websocket, ai
from app.telemetry import telemetry

# Load telemetry environment variables
load_dotenv(".env.telemetry")

# Set default OTEL endpoint if not set
if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317"

# Initialize telemetry BEFORE creating FastAPI app
telemetry.initialize("docuforge-ai", "1.0.0")

# Try to auto-instrument FastAPI if OpenTelemetry is available
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    
    # Auto-instrument requests and SQLAlchemy
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine)
    print("🔧 Auto-instrumentation enabled for HTTP requests and SQLAlchemy")
except ImportError:
    print("⚠️  OpenTelemetry auto-instrumentation not available")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DocuForge AI", version="1.0.0")

# Instrument FastAPI app after creation
try:
    FastAPIInstrumentor.instrument_app(app)
    print("🔧 FastAPI auto-instrumentation enabled")
except NameError:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {"message": "DocuForge AI Backend"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}