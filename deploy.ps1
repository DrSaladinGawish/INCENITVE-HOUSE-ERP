# IncentiveHouse ERP v2.2.2 - Docker Deploy Script
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ROOT

Write-Host "=== IncentiveHouse ERP v2.2.2 Deploy ===" -ForegroundColor Cyan

# 1. Verify Python
$pyVer = python --version 2>&1
Write-Host "Python: $pyVer" -ForegroundColor Green

# 2. Verify app import
python -c "from app.main import app; print(f'OK - {len(app.routes)} routes')"
if (-not $?) { Write-Host "Import failed!" -ForegroundColor Red; exit 1 }

# 3. Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
python -m pytest tests/ -v --tb=short 2>&1
if (-not $?) { Write-Host "Tests failed!" -ForegroundColor Red; exit 1 }

# 4. Build Docker
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker compose build

# 5. Run
Write-Host "Starting container on port 9001..." -ForegroundColor Green
docker compose up -d

# 6. Verify
Start-Sleep -Seconds 3
$resp = curl.exe -s http://localhost:9001/health 2>$null
Write-Host "Health check: $resp" -ForegroundColor Green
Write-Host "=== Done! Server at http://localhost:9001 ===" -ForegroundColor Cyan
