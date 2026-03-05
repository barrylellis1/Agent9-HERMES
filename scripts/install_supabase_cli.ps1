# Download and install Supabase CLI binary for Windows
$release = Invoke-RestMethod 'https://api.github.com/repos/supabase/cli/releases/latest'
Write-Host "Latest version: $($release.tag_name)"

$asset = $release.assets | Where-Object { $_.name -eq 'supabase_windows_amd64.tar.gz' } | Select-Object -First 1
Write-Host "Downloading: $($asset.name)"

$tarPath = [System.IO.Path]::Combine($env:TEMP, 'supabase_windows_amd64.tar.gz')
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $tarPath -UseBasicParsing
Write-Host "Downloaded to $tarPath"

# Use Windows native tar.exe (not Git Bash tar)
$extractDir = [System.IO.Path]::Combine($env:TEMP, 'supabase_extract')
New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
$winTar = 'C:\Windows\System32\tar.exe'
& $winTar -xzf $tarPath -C $extractDir
Write-Host "Extracted to $extractDir"

# Find the exe
Get-ChildItem $extractDir -Recurse | ForEach-Object { Write-Host "  $($_.FullName)" }
$exePath = Get-ChildItem -Path $extractDir -Filter 'supabase.exe' -Recurse | Select-Object -First 1 -ExpandProperty FullName
if (-not $exePath) {
    # try without .exe (Linux-style binary named just 'supabase')
    $exePath = Get-ChildItem -Path $extractDir -Filter 'supabase' -Recurse | Select-Object -First 1 -ExpandProperty FullName
}
Write-Host "Binary: $exePath"

$dest = 'C:\Users\Blell\Agent9-HERMES\supabase.exe'
Copy-Item $exePath $dest -Force
Write-Host "Installed to $dest"
& $dest --version
