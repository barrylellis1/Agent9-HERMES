# Agent9 / Decision Studio — Backend API
# Deploys on Railway, Render, or any Docker host
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ src/
COPY workflow_definitions/ workflow_definitions/
COPY .env.production.template .env.production.template

# Registry references (YAML-backed fallback data)
COPY src/registry_references/ src/registry_references/

# Port (Railway and Render set PORT env var)
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

# Start — use PORT env var for Railway/Render compatibility
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
