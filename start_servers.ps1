# Agent9-APOLLO Server Startup Script (PowerShell)
# This script automates startup of FastAPI backend and Streamlit UI.

# Kill any process using ports 8000 (API) or 8501/8503 (UI)
Write-Host "Killing any process on ports 8000, 8501, and 8503..." -ForegroundColor Yellow
$ports = @(8000, 8501, 8503)
foreach ($port in $ports) {
    $procIds = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $procIds) {
        if ($procId) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "Killed process $procId on port $port" -ForegroundColor DarkYellow
            } catch {}
        }
    }
}
Start-Sleep -Seconds 2

# Activate venv (for subprocesses)
$venvPath = Join-Path $PSScriptRoot '.venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'
$streamlitExe = Join-Path $venvPath 'Scripts\streamlit.exe'

# Start FastAPI backend (uvicorn) in new window if app module exists
$apiMainPath = Join-Path $PSScriptRoot 'src\api\main.py'
if (Test-Path $apiMainPath) {
    Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; & '$pythonExe' -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
} else {
    Write-Host "Skipping FastAPI backend startup: src/api/main.py not found" -ForegroundColor Yellow
}

Start-Sleep -Seconds 3

# Start Streamlit UI in new window (simple Decision Studio UI)
Write-Host "Starting Streamlit UI on port 8501..." -ForegroundColor Green
$uiPath = Join-Path $PSScriptRoot 'src\views\decision_studio_ui.py'
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; & '$streamlitExe' run `"$uiPath`" --server.port 8501"

Write-Host "Servers started successfully!" -ForegroundColor Magenta
Write-Host "API Server: http://localhost:8000" -ForegroundColor White
Write-Host "Streamlit UI: http://localhost:8501" -ForegroundColor White
Write-Host "Press Ctrl+C in the respective windows to stop the servers." -ForegroundColor Yellow
