# Environment Setup Guide

## Clean Virtual Environment Setup

To avoid dependency conflicts with global packages, use a clean virtual environment for this project.

### Step 1: Create Clean Virtual Environment

```bash
# Create a new virtual environment
python -m venv venv_clean

# Activate the environment
source venv_clean/bin/activate  # On macOS/Linux
# or
venv_clean\Scripts\activate     # On Windows
```

### Step 2: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 3: Install Dependencies

Install packages in this order to avoid conflicts:

```bash
# Core web framework dependencies
pip install fastapi uvicorn python-multipart websockets sqlalchemy alembic python-dotenv pydantic pydantic-settings

# AI and HTTP libraries
pip install openai anthropic httpx google-cloud-aiplatform aiofiles aiohttp

# Document processing and testing
pip install python-docx python-pptx reportlab google-auth Pillow numpy pytest pytest-asyncio

# OpenTelemetry (monitoring)
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation opentelemetry-exporter-otlp
pip install opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests opentelemetry-instrumentation-aiohttp-client opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-sqlite3 opentelemetry-instrumentation-logging

# Vertex AI SDK
pip install vertexai
```

### Step 4: Verify Installation

```bash
# Check for dependency conflicts
pip check

# Test the application
python -c "from app.main import app; print('✅ Application imports successfully')"
```

### Step 5: Run the Application

```bash
# Start the development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Make sure your `.env` file contains:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_SERVICE_ACCOUNT_FILE=./path-to-service-account.json
DEFAULT_LLM_PROVIDER=google
DEFAULT_GOOGLE_MODEL=gemini-2.5-pro

# API Keys (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=docuforge-ai
```

## Dependency Versions Installed

The clean environment installs these updated versions that resolve all conflicts:

- **fastapi**: 0.116.0 (updated from 0.104.1)
- **uvicorn**: 0.35.0 (updated from 0.24.0)
- **websockets**: 15.0.1 (updated from 12.0)
- **httpx**: 0.28.1 (updated from 0.24.1)
- **anyio**: 4.9.0 (updated from 3.7.1)
- **pydantic**: 2.11.7 (updated from 2.5.0)
- **sqlalchemy**: 2.0.41 (updated from 2.0.23)
- **alembic**: 1.16.4 (updated from 1.12.1)

All other packages are automatically updated to compatible versions.

## Benefits of Clean Environment

✅ **No dependency conflicts**
✅ **Latest compatible versions**
✅ **Isolated from global packages**
✅ **Reproducible across systems**
✅ **All features working correctly**

## Troubleshooting

If you encounter issues:

1. **Delete and recreate the environment**:
   ```bash
   rm -rf venv_clean
   python -m venv venv_clean
   ```

2. **Ensure you're using the clean environment**:
   ```bash
   which python  # Should point to venv_clean/bin/python
   ```

3. **Check for missing dependencies**:
   ```bash
   pip check
   ```