# This script restarts the NEW Agent9 Decision Studio (React + FastAPI)
# It kills existing processes on ports 8000 (API) and 5173 (UI) and starts them fresh.

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        return $false
    } catch {
        return $true
    } finally {
        if ($listener) { $listener.Stop() }
    }
}

# Function to kill process on a port
function Kill-Port {
    param([int]$Port)
    if (Test-PortInUse -Port $Port) {
        Write-Host "Port $Port is in use. Killing process..." -ForegroundColor Yellow
        netstat -ano | findstr ":$Port" | ForEach-Object {
            $line = $_ -replace '\s+', ' '
            $parts = $line -split ' '
            $pidVal = $parts[-1]
            if ($pidVal -match '^\d+$') {
                Write-Host "Killing PID $pidVal" -ForegroundColor DarkGray
                Stop-Process -Id $pidVal -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 1
    }
}

Write-Host "=== Restarting Agent9 Decision Studio (Consumer Grade) ===" -ForegroundColor Cyan

# 1. Kill Ports
Kill-Port -Port 8000
Kill-Port -Port 5173

# 2. Start Backend (FastAPI)
Write-Host "Starting FastAPI Backend (Port 8000)..." -ForegroundColor Green
$venvPath = Join-Path $PSScriptRoot '.venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'

# We start a new PowerShell window for the backend so it persists and logs
# Run uvicorn directly to match restart_app.ps1 pattern
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; & '$pythonExe' -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

# 3. Start Frontend (React/Vite)
Write-Host "Starting React Frontend (Port 5173)..." -ForegroundColor Green
# We start a new PowerShell window for the frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\decision-studio-ui'; npm run dev"

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:5173"
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Done! Please wait a few seconds for servers to spin up."
