# Clean restart script for Agent9
# This script kills any processes that might be locking resources and ensures a clean environment

Write-Host "Cleaning up environment for Agent9..."

# Kill any Python processes that might be locking the database
Write-Host "Killing any Python processes that might be locking resources..."
Get-Process | Where-Object { $_.ProcessName -eq "python" } | ForEach-Object {
    Write-Host "Killing process $($_.Id): $($_.ProcessName)"
    Stop-Process -Id $_.Id -Force
}

# Kill any Streamlit processes
Write-Host "Killing any Streamlit processes..."
Get-Process | Where-Object { $_.ProcessName -eq "streamlit" } | ForEach-Object {
    Write-Host "Killing process $($_.Id): $($_.ProcessName)"
    Stop-Process -Id $_.Id -Force
}

# Wait a moment to ensure processes are terminated
Start-Sleep -Seconds 2

# Check if database file exists and is locked
$dbPath = "data/agent9-hermes.duckdb"
if (Test-Path $dbPath) {
    try {
        # Try to open the file to see if it's locked
        $fileStream = [System.IO.File]::Open($dbPath, 'Open', 'Read', 'None')
        $fileStream.Close()
        Write-Host "Database file is not locked."
    }
    catch {
        Write-Host "Warning: Database file appears to be locked. Attempting to create a backup and use a new file."
        
        # Create a backup of the current database
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "data/agent9-hermes_backup_$timestamp.duckdb"
        
        # Copy the file (this might fail if it's completely locked)
        try {
            Copy-Item -Path $dbPath -Destination $backupPath -ErrorAction Stop
            Write-Host "Created backup at $backupPath"
        }
        catch {
            Write-Host "Could not create backup. File is completely locked."
        }
        
        # Rename the original file to force creation of a new one
        try {
            Rename-Item -Path $dbPath -NewName "agent9-hermes_locked_$timestamp.duckdb" -ErrorAction Stop
            Write-Host "Renamed locked database file."
        }
        catch {
            Write-Host "Could not rename locked database file."
        }
    }
}

Write-Host "Environment cleanup complete."
Write-Host "You can now start the application with a clean environment."
