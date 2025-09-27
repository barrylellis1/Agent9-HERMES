# This script automates the process of restarting the Streamlit application.
# It first forcefully terminates any running Streamlit processes and then starts the app again.

param(
    [ValidateSet("stable", "next")]
    [string]$Channel = "stable"
)

# Set runtime channel env var for child processes (without touching .env)
$env:A9_DS_CHANNEL = $Channel
Write-Host "Decision Studio channel: $Channel" -ForegroundColor Cyan

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port = 8501
    )
    
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        return $false
    } catch {
        return $true
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

# Stop any currently running Streamlit server
Write-Host "Attempting to stop any running Streamlit servers..."
try {
    # Try to kill streamlit processes
    $streamlitProcesses = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
    if ($streamlitProcesses) {
        $streamlitProcesses | ForEach-Object { 
            Write-Host "Killing process $($_.Id)"
            Stop-Process -Id $_.Id -Force
        }
    } else {
        Write-Host "No streamlit processes found"
    }
    
    # Wait to ensure processes are fully terminated
    Start-Sleep -Seconds 2
} catch {
    Write-Host "Error stopping processes: $_"
}

# Check if port 8501 is still in use
if (Test-PortInUse -Port 8501) {
    Write-Host "Warning: Port 8501 is still in use. Attempting to free it..."
    # Try more aggressive termination
    netstat -ano | findstr :8501 | ForEach-Object {
        $line = $_ -replace '\s+', ' '
        $processId = ($line -split ' ')[-1]
        if ($processId -match '\d+') {
            Write-Host "Killing process using port 8501: $processId"
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

# Also ensure API port 8000 is free
if (Test-PortInUse -Port 8000) {
    Write-Host "Warning: Port 8000 is still in use. Attempting to free it..."
    # Try more aggressive termination
    netstat -ano | findstr :8000 | ForEach-Object {
        $line = $_ -replace '\s+', ' '
        $processId = ($line -split ' ')[-1]
        if ($processId -match '\d+') {
            Write-Host "Killing process using port 8000: $processId"
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

# Prepare logs directory BEFORE starting so we can tee output
if (-not (Test-Path .\logs)) {
    New-Item -ItemType Directory -Path .\logs | Out-Null
}

# Start the Streamlit server and tee output to logs
Write-Host "Starting the Decision Studio UI..."
try {
    # Determine venv executables and start backend (FastAPI) first
    $venvPath = Join-Path $PSScriptRoot '.venv'
    $pythonExe = Join-Path $venvPath 'Scripts\python.exe'
    $apiMainPath = Join-Path $PSScriptRoot 'src\api\main.py'

    if (Test-Path $apiMainPath) {
        Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; & '$pythonExe' -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
    }

    # Build a unique log file path to avoid file locking across restarts
    $logFilePath = Join-Path $PSScriptRoot ("logs\\streamlit_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    # Activate the virtual environment in current shell (optional for current script scope)
    . .\.venv\Scripts\Activate.ps1
    # Compose the command to run in a new PowerShell process. Use single quotes to prevent premature variable expansion.
    $cmd = '$env:PYTHONUNBUFFERED=1; $env:STREAMLIT_LOG_LEVEL="info"; . .\.venv\Scripts\Activate.ps1; streamlit run decision_studio.py --logger.level=info *>&1 | Tee-Object -FilePath ' + ('"' + $logFilePath + '"') + ' -Append'
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
} catch {
    Write-Host "Error starting Decision Studio: $_"
}

# Give the app a moment to start
Start-Sleep -Seconds 5

# Wait a moment for the app to start
Start-Sleep -Seconds 3

# Show a message that the app is running
Write-Host "Decision Studio is running at http://localhost:8501"
Write-Host "Log file is available at $logFilePath"
Write-Host "Press Ctrl+C to stop viewing logs"

# Tail the streamlit log file to show real-time output
try {
    Get-Content $logFilePath -Wait
} catch {
    Write-Host "Stopped viewing logs"
}
