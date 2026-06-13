Set-Location D:\IncentiveHouse_ERP

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "IH-ERP Launcher v2.5.0" -ForegroundColor Cyan
Write-Host "IHF Pattern v1.0" -ForegroundColor Cyan
Write-Host (Get-Date) -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "`n[LAUNCHER] Import verification..." -ForegroundColor Yellow

$imports = @("app.main", "app.models", "app.routers", "app.services", "app.reports")
$failed = $false

foreach ($mod in $imports) {
    python -c "import $mod" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $mod" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $mod" -ForegroundColor Red
        $failed = $true
    }
}

if ($failed) {
    Write-Host "`n[LAUNCHER] IMPORT FAILED" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "`n[LAUNCHER] Starting server..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Start-Process "http://localhost:9001/api/v1/launcher/dashboard-v2"
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
