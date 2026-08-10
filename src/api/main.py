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
from src.api.routes.admin import router as admin_router
from src.api.routes.kpi_accountability import router as accountability_router
from src.api.routes.kpi_templates import router as kpi_templates_router
from src.api.routes.business_process_templates import router as business_process_templates_router
from src.api.routes.onboarding import router as onboarding_router

app = FastAPI(
    title="Agent9 API",
    version="0.1.0",
    description="Backend API for Agent9. Contains health and future MCP service endpoints.",
)

# CORS: allow_origins=["*"] is incompatible with allow_credentials=True (CORS spec).
# When FRONTEND_URL is set, use explicit origins + credentials.
# FRONTEND_URL supports comma-separated values for multiple domains.
# When not set (local dev), allow all origins but disable credentials.
_frontend_url = os.getenv("FRONTEND_URL", "").strip()
if _frontend_url:
    _cors_origins = [u.strip().rstrip("/") for u in _frontend_url.split(",") if u.strip()]
    _cors_origins += ["http://localhost:5173", "http://127.0.0.1:5173"]
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
app.include_router(admin_router)
app.include_router(accountability_router)
app.include_router(kpi_templates_router)
app.include_router(business_process_templates_router)
app.include_router(onboarding_router)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        await agent_runtime.initialize()
    except Exception:  # pragma: no cover - logged for diagnostics
        logging.getLogger(__name__).exception("Failed to initialize AgentRuntime during startup")


# Feature flags whose state is worth knowing from outside the box. Booleans only —
# never a value, so this can never leak a credential.
_REPORTED_FLAGS = (
    "SF_ENABLE_THEORY_MODERATOR",
    "SF_ENABLE_CRITIC_PASS",
    "SF_ENABLE_CAUSAL_GROUNDING",
    "SF_USE_STRUCTURED_OUTPUT",
)


@app.get("/healthz")
async def healthz():
    """Liveness, plus which gated features this deployment actually has on.

    WHY THE FLAGS ARE HERE
    ----------------------
    A decision to enable something is not the same as it being enabled, and we
    had no way to tell the two apart from outside. The Stage H A/B concluded
    "adopt the theory-guided moderator"; the flag was set locally and the
    conclusion was treated as shipped, with no way short of the hosting
    dashboard to check whether production agreed. The same blindness cost real
    time earlier the same day, when a code path was fixed, tested, and shipped
    before a live run showed it was never the path being executed.

    Booleans only. Reading the environment directly rather than an agent's
    resolved config is deliberate: this must answer "what did this container
    start with", and stay answerable even if agent bootstrap failed.
    """
    return JSONResponse({
        "status": "ok",
        "features": {
            name.lower().removeprefix("sf_"): os.getenv(name, "false").lower() == "true"
            for name in _REPORTED_FLAGS
        },
    })


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

# Test fixture routes — only mounted in test environments (never in production)
if os.getenv("APP_ENV") == "test":
    from src.api.routes.test_fixtures import router as test_fixtures_router
    app.include_router(test_fixtures_router, prefix="/api/v1")
    logging.getLogger(__name__).warning(
        "TEST FIXTURES ROUTER MOUNTED — do not run with APP_ENV=test in production"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
