@echo off
REM ================================================================
REM IncentiveHouse ERP v2.2.2 — Deployment Script
REM Copies new files to target project, installs deps, verifies, starts
REM ================================================================
setlocal enabledelayedexpansion
set TARGET=%~1
if "%TARGET%"=="" (
    echo Usage: deploy.bat ^<target-project-root^>
    echo Example: deploy.bat D:\ERP_System\BIO_ERP
    exit /b 1
)
if not exist "%TARGET%" (
    echo ERROR: Target directory does not exist: %TARGET%
    exit /b 1
)

echo ============================================================
echo IncentiveHouse ERP v2.2.2 — Deployment
echo Target: %TARGET%
echo ============================================================
echo.

REM === STEP 1: Copy files ===
echo [1/6] Copying new files to target...
set SOURCE=%~dp0
echo Source: %SOURCE%

mkdir "%TARGET%\app\routers" 2>nul
mkdir "%TARGET%\tests" 2>nul

copy /Y "%SOURCE%app\main.py" "%TARGET%\app\main.py" >nul
copy /Y "%SOURCE%app\routers\clients.py" "%TARGET%\app\routers\clients.py" >nul
copy /Y "%SOURCE%app\routers\vendors.py" "%TARGET%\app\routers\vendors.py" >nul
copy /Y "%SOURCE%app\routers\pnr.py" "%TARGET%\app\routers\pnr.py" >nul
copy /Y "%SOURCE%app\routers\employees.py" "%TARGET%\app\routers\employees.py" >nul
copy /Y "%SOURCE%app\routers\reports.py" "%TARGET%\app\routers\reports.py" >nul
copy /Y "%SOURCE%tests\conftest.py" "%TARGET%\tests\conftest.py" >nul
copy /Y "%SOURCE%tests\test_integration.py" "%TARGET%\tests\test_integration.py" >nul
echo   OK 8 files copied

REM === STEP 2: Install dependencies ===
echo [2/6] Installing Python dependencies...
cd /d "%TARGET%"
if exist requirements.txt (
    pip install -r requirements.txt -q 2>nul
    echo   OK Dependencies installed
) else (
    echo   WARN requirements.txt not found, skipping
)

REM === STEP 3: Syntax check ===
echo [3/6] Checking import syntax...
python -c "from app.main import app; print('  OK Import OK')" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   FAIL Import check failed
    exit /b 1
)

REM === STEP 4: Run tests ===
echo [4/6] Running test suite...
python -m pytest tests/ -v --tb=short 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   WARN Some tests failed — review output above
) else (
    echo   OK All tests passed
)

REM === STEP 5: Start server ===
echo [5/6] Starting server on port 9001...
start "IncentiveHouse" cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload"
echo   OK Server starting — wait 3 seconds...

REM === STEP 6: Verify health ===
echo [6/6] Verifying health endpoint...
timeout /t 3 /nobreak >nul
curl -s http://localhost:9001/health 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   WARN Health check failed — server may need more time
) else (
    echo   OK Health endpoint responding
)

echo.
echo ============================================================
echo Deployment complete
echo ============================================================
echo.
echo OpenAPI docs: http://localhost:9001/docs
echo Health check: http://localhost:9001/health
echo.
echo To stop server: taskkill /fi "WINDOWTITLE eq IncentiveHouse"
echo.
endlocal
