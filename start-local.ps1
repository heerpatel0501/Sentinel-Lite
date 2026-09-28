$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

Write-Host "Stopping any stale Sentinel-Lite processes on ports 8000 and 3000..."
$ports = @(8000, 3000)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            if ($conn.OwningProcess) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Write-Host "Starting backend on http://localhost:8000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$backendDir'; $env:PYTHONPATH='.'; py -m uvicorn main:app --host 0.0.0.0 --port 8000"
)

Write-Host "Starting frontend on http://localhost:3000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$frontendDir'; npm --prefix . run dev -- --host 0.0.0.0 --port 3000"
)

Write-Host "Sentinel-Lite startup initiated."
Write-Host "Open http://localhost:3000/ in your browser."
