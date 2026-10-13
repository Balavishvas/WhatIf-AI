$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend "venv\Scripts\python.exe"

Write-Host ""
Write-Host "  WHATIF AI  |  LOCAL LAUNCHER" -ForegroundColor Green
Write-Host "  ----------------------------"
if (-not (Test-Path $python)) {
    Write-Host "Backend virtual environment not found. Creating it..." -ForegroundColor Yellow
    py -3 -m venv (Join-Path $backend "venv")
    if ($LASTEXITCODE -ne 0) { throw "Python 3 was not found. Install Python 3.11+ and enable its PATH option, then run this script again." }
}
Write-Host "[1/4] Checking backend dependencies..." -ForegroundColor Cyan
& $python -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw "Could not prepare pip in backend\venv." }
& $python -m pip install -r (Join-Path $backend "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Read the pip error above." }

$healthUrl = "http://127.0.0.1:8000/health"
$backendReady = $false
try {
    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
    if ($health.status -eq "ok") { $backendReady = $true }
} catch {}

if (-not $backendReady) {
    Write-Host "[2/4] Starting FastAPI on port 8000..." -ForegroundColor Cyan
    $backendCommand = "Set-Location '$backend'; & '$python' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand)
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
            if ($health.status -eq "ok") { $backendReady = $true; break }
        } catch {}
    }
}
if (-not $backendReady) { throw "Backend did not become healthy. Check the separate backend terminal for its error." }
Write-Host "      Backend healthy." -ForegroundColor Green

Write-Host "[3/4] Starting frontend on port 5500..." -ForegroundColor Cyan
$frontendReady = $false
try {
    $probe = Invoke-WebRequest -Uri "http://127.0.0.1:5500/" -TimeoutSec 2 -UseBasicParsing
    if ($probe.StatusCode -eq 200) { $frontendReady = $true }
} catch {}
if (-not $frontendReady) {
    $frontendCommand = "Set-Location '$root'; & '$python' -m http.server 5500 --directory '$frontend' --bind 127.0.0.1"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand)
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Milliseconds 700
        try {
            $probe = Invoke-WebRequest -Uri "http://127.0.0.1:5500/" -TimeoutSec 2 -UseBasicParsing
            if ($probe.StatusCode -eq 200) { $frontendReady = $true; break }
        } catch {}
    }
}
if (-not $frontendReady) { throw "Frontend did not respond on port 5500. Check whether another app is using that port." }

Write-Host "[4/4] Opening WhatIf AI..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:5500"
Start-Sleep -Milliseconds 800
Start-Process "http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Ready! Frontend: http://127.0.0.1:5500" -ForegroundColor Green
Write-Host "       Backend:  http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host "       Swagger:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Leave the two server windows open while using the app." -ForegroundColor Yellow
