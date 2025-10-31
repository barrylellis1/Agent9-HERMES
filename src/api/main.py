import logging
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.runtime import AgentRuntime
from src.api.routes.registry import router as registry_router
from src.api.routes.workflows import router as workflows_router

app = FastAPI(
    title="Agent9 API",
    version="0.1.0",
    description="Backend API for Agent9. Contains health and future MCP service endpoints.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent_runtime = AgentRuntime()
app.include_router(registry_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")


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
