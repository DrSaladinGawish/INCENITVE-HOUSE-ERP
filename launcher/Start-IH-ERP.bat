@echo off
setlocal enabledelayedexpansion

echo ============================================
echo IH-ERP Launcher v2.5.0
echo IHF Pattern v1.0
echo %date% %time%
echo ============================================
echo.

cd /d D:\IncentiveHouse_ERP

echo [LAUNCHER] Step 1: Import verification...
echo.

python -c "import app.main; print('  [OK] main.py')" 2>nul
if errorlevel 1 goto :import_fail

python -c "import app.models; print('  [OK] models.py')" 2>nul
if errorlevel 1 goto :import_fail

python -c "import app.routers; print('  [OK] routers')" 2>nul
if errorlevel 1 goto :import_fail

python -c "import app.services; print('  [OK] services')" 2>nul
if errorlevel 1 goto :import_fail

python -c "import app.reports; print('  [OK] reports')" 2>nul
if errorlevel 1 goto :import_fail

echo.
echo [LAUNCHER] All imports verified. Starting server...
echo ============================================
echo.

uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
goto :end

:import_fail
echo.
echo [LAUNCHER] IMPORT FAILED
echo Server start aborted.
echo Fix the error above and retry.
echo ============================================
pause
exit /b 1

:end
