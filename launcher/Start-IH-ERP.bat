@echo off
setlocal

echo ============================================
echo IH-ERP Launcher v2.5.0
echo IHF Pattern v1.0
echo %date% %time%
echo ============================================
echo.

cd /d D:\IncentiveHouse_ERP

echo [LAUNCHER] Import verification...
python -c "import app.main; print('  [OK] main.py')" 2>nul || goto :error
python -c "import app.models; print('  [OK] models.py')" 2>nul || goto :error
python -c "import app.routers; print('  [OK] routers')" 2>nul || goto :error
python -c "import app.services; print('  [OK] services')" 2>nul || goto :error
python -c "import app.reports; print('  [OK] reports')" 2>nul || goto :error

echo.
echo [LAUNCHER] Starting server...
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
goto :end

:error
echo.
echo [LAUNCHER] IMPORT FAILED
pause
exit /b 1

:end
