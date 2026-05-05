# Agent9 / Decision Studio — Backend API
# Deploys on Railway, Render, or any Docker host
FROM python:3.11-slim

WORKDIR /app

# Python dependencies — prefer binary wheels (no C compiler needed)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Application code
COPY src/ src/
COPY workflow_definitions/ workflow_definitions/
COPY .env.production.template .env.production.template

# Port (Railway and Render set PORT env var)
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

# Start — use PORT env var for Railway/Render compatibility
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
