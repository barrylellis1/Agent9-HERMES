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

# 1c. Close windows left behind by previous runs.
# Kill-Port kills the SERVER, but the -NoExit shell hosting it survives its child,
# so every run left two dead windows behind. Nine runs had accumulated eighteen.
# Matched on the exact command lines this script spawns, so ordinary shells the
# user opened themselves are never touched.
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | ForEach-Object {
    $cmd = $_.CommandLine
    if ($cmd -and $_.ProcessId -ne $PID -and (
            $cmd -like '*-m uvicorn src.api.main:app*' -or
            $cmd -like '*decision-studio-ui*npm run dev*' -or
            $cmd -like '*A9 backend log*')) {
        Write-Host "Closing stale dev window PID $($_.ProcessId)" -ForegroundColor DarkGray
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

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

$logDir = Join-Path $PSScriptRoot 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$backendOut = Join-Path $logDir 'backend.out.log'
$backendLog = Join-Path $logDir 'backend.log'   # uvicorn logs to stderr

# The backend must NOT own a console.
#
# It used to run inside a -NoExit window. Windows consoles default to QuickEdit
# mode, so a single stray click inside that window selects text and PAUSES the
# screen buffer — and every subsequent write to stdout blocks indefinitely. The
# server then wedges mid logging.emit while still holding the listening socket,
# so the port looks healthy, connections are accepted, and every request hangs
# until it times out. Observed exactly that: three py-spy samples two seconds
# apart, all identical, all parked in logging.emit inside an HTTP send. The UI
# sat on "Loading identities..." and the live e2e run died at login.
#
# Writing to a file instead means a paused console can no longer block the
# server. The log viewer below is a separate process; pausing THAT is harmless.
#
# --reload-dir src is the other half. Bare --reload makes the supervisor walk
# every file under the repo root looking for .py files — 142,596 of them here,
# including node_modules, .venv and playwright artifacts — which pinned a core
# at 100% (1,513 seconds of CPU in ~25 minutes of uptime). src/ is the only
# tree whose .py files should trigger a reload.
Start-Process -FilePath $pythonExe `
    -ArgumentList '-m','uvicorn','src.api.main:app','--host','0.0.0.0','--port','8000','--reload','--reload-dir','src' `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $backendOut `
    -RedirectStandardError $backendLog `
    -WindowStyle Hidden

# Separate viewer so logs stay visible without the server depending on a console.
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "`$Host.UI.RawUI.WindowTitle = 'A9 backend log (viewer only - safe to close)'; Get-Content -Path '$backendLog' -Wait -Tail 40"

# 3. Start Frontend (React/Vite)
# The live Playwright config (playwright.live.config.ts) runs its OWN vite on 5173
# with reuseExistingServer:false, because a stale dev server would silently test
# old frontend code. So during an e2e run the port is legitimately taken by the
# harness — starting a second vite is not something to retry or force, it is a
# signal that a test owns the port. Detect that and skip, rather than spawning a
# window that immediately dies with a strictPort error the user has to interpret.
$feBusy = $null
try { $feBusy = Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction Stop } catch {}
if ($feBusy) {
    Write-Host "Port 5173 already serving (likely a Playwright live run) - leaving it alone." -ForegroundColor Yellow
    Write-Host "  If that is NOT intentional, stop the owning process and re-run this script." -ForegroundColor DarkGray
} else {
    Write-Host "Starting React Frontend (Port 5173)..." -ForegroundColor Green
    # --strictPort: vite's default is to silently increment to the next free port when
    # 5173 is taken, while this script keeps printing "Frontend: http://localhost:5173".
    # A run that overlapped a surviving vite left the app served on 5174 with nothing
    # reporting that, so the advertised URL was simply dead. Fail loudly instead.
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\decision-studio-ui'; npm run dev -- --strictPort"
}

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:5173"
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Done! Please wait a few seconds for servers to spin up."
