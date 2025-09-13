from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Agent9 API",
    version="0.1.0",
    description="Backend API for Agent9. Contains health and future MCP service endpoints.",
)


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


@app.get("/")
async def root():
    return {"service": "agent9-api", "message": "Agent9 API is running"}


# NOTE: MCP service endpoints will be added under /mcp when the service is introduced.
# from src.api.mcp_service import router as mcp_router
# app.include_router(mcp_router, prefix="/mcp")
