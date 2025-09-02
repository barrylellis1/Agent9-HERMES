# This script automates the process of restarting the Streamlit application.
# It first forcefully terminates any running Streamlit processes and then starts the app again.

# Stop any currently running Streamlit server
Write-Host "Attempting to stop any running Streamlit servers..."
taskkill /F /IM streamlit.exe /T | Out-Null

# Start the Streamlit server
Write-Host "Starting the Decision Studio UI..."
# Activate the virtual environment and run the app
. .\.venv\Scripts\Activate.ps1
# Start the Streamlit server in the background
Start-Process powershell -ArgumentList "-NoExit", "-Command", ". .\.venv\Scripts\Activate.ps1; streamlit run decision_studio.py"

# Give the app a moment to start and create the log file
Start-Sleep -Seconds 5

# Create logs directory if it doesn't exist
if (-not (Test-Path .\logs)) {
    New-Item -ItemType Directory -Path .\logs | Out-Null
}

# Create log file if it doesn't exist
if (-not (Test-Path .\logs\agent9.log)) {
    New-Item -ItemType File -Path .\logs\agent9.log | Out-Null
}

# Tail the log file to show real-time output
Get-Content .\logs\agent9.log -Wait
