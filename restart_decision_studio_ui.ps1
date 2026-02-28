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

# 1a. Kill any non-venv Python processes that may be holding the DuckDB file open
Write-Host "Checking for stale Python processes holding DuckDB..." -ForegroundColor Cyan
$venvScripts = Join-Path $PSScriptRoot '.venv\Scripts'
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $exePath = $_.MainModule.FileName
        if ($exePath -notlike "*\.venv\*") {
            Write-Host "Killing non-venv Python PID $($_.Id): $exePath" -ForegroundColor DarkGray
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Can't read process path (permissions) — skip silently
    }
}
Start-Sleep -Seconds 1

# 1b. Kill Ports
Kill-Port -Port 8000
Kill-Port -Port 5173

# 1.4 Ensure Docker is Running
Write-Host "Checking Docker status..." -ForegroundColor Cyan
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not responding. Attempting to start Docker Desktop..." -ForegroundColor Yellow
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        
        # Wait for Docker to come up
        Write-Host "Waiting for Docker to start (this may take a minute)..." -NoNewline
        $retries = 60 # 2 minutes max
        while ($retries -gt 0) {
            docker info > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`nDocker started successfully." -ForegroundColor Green
                break
            }
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
            $retries--
        }
        if ($retries -eq 0) {
             Write-Host "`nTimeout waiting for Docker. Proceeding, but Supabase will likely fail." -ForegroundColor Red
        }
    } else {
         Write-Host "Docker Desktop not found at default location ($dockerPath). Please ensure it is running." -ForegroundColor Red
    }
} else {
    Write-Host "Docker is running." -ForegroundColor Green
}

# 1.5 Check Supabase Status
# Resolve supabase CLI: prefer system PATH, fall back to local binary in project root
Write-Host "Checking Supabase Status..." -ForegroundColor Cyan
$supabaseCli = $null
if (Get-Command supabase -ErrorAction SilentlyContinue) {
    $supabaseCli = "supabase"
} elseif (Test-Path (Join-Path $PSScriptRoot "supabase.exe")) {
    $supabaseCli = Join-Path $PSScriptRoot "supabase.exe"
}

if ($supabaseCli) {
    try {
        $null = & $supabaseCli status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Supabase is not running. Attempting to start..." -ForegroundColor Yellow
            & $supabaseCli start
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Error: Failed to start Supabase. Please check Docker Desktop status." -ForegroundColor Red
                Write-Host "Continuing anyway, but backend may fail if it relies on Supabase..." -ForegroundColor DarkYellow
            } else {
                Write-Host "Supabase started successfully." -ForegroundColor Green
            }
        } else {
            Write-Host "Supabase is running." -ForegroundColor Green
        }
    } catch {
        Write-Host "Warning: Error checking Supabase status: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "Warning: Supabase CLI not found (checked PATH and .\supabase.exe). Skipping Supabase check." -ForegroundColor Yellow
}

# 1.6 Registry Sync - DEPRECATED (2026-02-19)
# All registries now live in Supabase. YAML seed scripts are deprecated.
# To force a recovery sync, run: python scripts/sync_yaml_to_supabase.py --force
Write-Host "Skipping YAML-to-Supabase sync (deprecated - registries read directly from Supabase)." -ForegroundColor DarkGray

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
