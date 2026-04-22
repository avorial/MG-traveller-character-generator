# run.ps1
# Start the Traveller creator on http://localhost:2026
#
# Usage:
#   .\run.ps1              - start detached, print URL
#   .\run.ps1 -Foreground  - stream logs instead of detaching
#   .\run.ps1 -Stop        - stop the container
#   .\run.ps1 -Port 12345  - override the port (rare)

param(
    [int]$Port = 2026,
    [switch]$Foreground,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

if ($Stop) {
    Write-Host "Stopping traveller-creator..." -ForegroundColor Yellow
    docker compose down
    exit 0
}

Write-Host "Using port: $Port" -ForegroundColor Cyan
$env:HOST_PORT = "$Port"

# Tear down any previous instance so the new port actually takes effect
docker compose down 2>$null | Out-Null

if ($Foreground) {
    docker compose up --build
} else {
    docker compose up -d --build
    Start-Sleep -Seconds 2
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host "  Traveller creator is live at:"                       -ForegroundColor Green
    Write-Host "    http://localhost:$Port"                             -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Stream logs:   docker compose logs -f traveller" -ForegroundColor DarkGray
    Write-Host "Stop:          .\run.ps1 -Stop"                   -ForegroundColor DarkGray
}
