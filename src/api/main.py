from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from typing import List

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


@app.get("/agents/state")
async def agents_state() -> List[dict]:
    return [
        {
            "name": "A9_Situation_Awareness_Agent",
            "state": "idle",
            "last_activity": "2025-10-12T18:13:00Z",
        },
        {
            "name": "A9_Data_Product_Agent",
            "state": "processing",
            "last_activity": "2025-10-12T18:12:30Z",
        },
        {
            "name": "A9_Solution_Finder_Agent",
            "state": "waiting",
            "last_activity": "2025-10-12T18:11:45Z",
        },
    ]


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


@app.get("/")
async def root():
    return {"service": "agent9-api", "message": "Agent9 API is running"}


# NOTE: MCP service endpoints will be added under /mcp when the service is introduced.
# from src.api.mcp_service import router as mcp_router
# app.include_router(mcp_router, prefix="/mcp")
