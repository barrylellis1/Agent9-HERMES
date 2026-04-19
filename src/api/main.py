import json
import logging
import os
import tempfile
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Materialize GCP service-account JSON from env var → temp file
# Railway/Render can't mount files, so we accept the JSON as a string env var
_gcp_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON", "")
if _gcp_json and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        _creds = json.loads(_gcp_json)
        _tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(_creds, _tmp)
        _tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _tmp.name
        logging.getLogger(__name__).info("GCP credentials materialized to %s", _tmp.name)
    except Exception as _exc:
        logging.getLogger(__name__).warning("Failed to materialize GCP credentials: %s", _exc)

from src.api.runtime import AgentRuntime
from src.api.routes.registry import router as registry_router
from src.api.routes.workflows import router as workflows_router
from src.api.routes.upload import router as upload_router
from src.api.routes.connection_profiles import router as connection_profiles_router
from src.api.routes.kpi_assistant import router as kpi_assistant_router
from src.api.routes.value_assurance import router as value_assurance_router
from src.api.routes.assessments import router as assessments_router
from src.api.routes.pib import router as pib_router
from src.api.routes.company_profile import router as company_profile_router

app = FastAPI(
    title="Agent9 API",
    version="0.1.0",
    description="Backend API for Agent9. Contains health and future MCP service endpoints.",
)

# CORS: allow_origins=["*"] is incompatible with allow_credentials=True (CORS spec).
# When FRONTEND_URL is set, use explicit origins + credentials.
# When not set (local dev), allow all origins but disable credentials.
_frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
if _frontend_url:
    _cors_origins = [_frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"]
    _allow_credentials = True
else:
    _cors_origins = ["*"]
    _allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent_runtime = AgentRuntime()
app.include_router(registry_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(connection_profiles_router)
app.include_router(kpi_assistant_router)
app.include_router(value_assurance_router)
app.include_router(assessments_router)
app.include_router(pib_router)
app.include_router(company_profile_router)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        await agent_runtime.initialize()
    except Exception:  # pragma: no cover - logged for diagnostics
        logging.getLogger(__name__).exception("Failed to initialize AgentRuntime during startup")


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


@app.get("/")
async def root():
    return {"service": "agent9-api", "message": "Agent9 API is running"}


@app.get("/agents/state")
async def agents_state() -> List[Dict[str, str]]:
    try:
        return await agent_runtime.get_agent_states()
    except Exception as exc:  # pragma: no cover - surface errors to caller
        logging.getLogger(__name__).exception("Unable to fetch agent states")
        raise HTTPException(status_code=500, detail=str(exc))


# NOTE: MCP service endpoints will be added under /mcp when the service is introduced.
# from src.api.mcp_service import router as mcp_router
# app.include_router(mcp_router, prefix="/mcp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
