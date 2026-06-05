@echo off
REM IHE-ERP Database Migration Runner v3.0
setlocal EnableDelayedExpansion
echo.
echo  ============================================
echo   IHE-ERP Migration Runner v3.0
echo  ============================================
echo.
set "PKG_DIR=%~dp0"
set "MIGRATION_DIR=%PKG_DIR%migrations"
set "SQL_DIR=%PKG_DIR%sql"
set "LOG_FILE=%PKG_DIR%migration_log_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "LOG_FILE=%LOG_FILE: =0%"

echo [1/9] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 ( echo [ERROR] Python not found. Install Python 3.11+. & pause & exit /b 1 )
echo [OK] Python found.

echo [2/9] Checking required packages...
python -c "import pyodbc, sqlalchemy, pydantic, pandas" >nul 2>&1
if errorlevel 1 ( echo [ERROR] Missing packages. Run: pip install pyodbc sqlalchemy pydantic pandas openpyxl & pause & exit /b 1 )
echo [OK] All packages installed.

echo [3/9] Loading environment...
if exist "%PKG_DIR%.env" ( for /f "usebackq tokens=1,2 delims==" %%a in ("%PKG_DIR%.env") do set "%%a=%%b" & echo [OK] .env loaded. ) else ( echo [WARN] No .env file found. Using defaults. )

echo [4/9] Testing SQL Server connection...
python -c "import pyodbc, os; c = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + os.getenv('SQL_SERVER','localhost') + ';DATABASE=' + os.getenv('SQL_DATABASE','IHE_ERP') + ';UID=' + os.getenv('SQL_USERNAME','sa') + ';PWD=' + os.getenv('SQL_PASSWORD','IHE_ERP_2024!'), timeout=10); print('[OK] Connected.'); c.close()"
if errorlevel 1 ( echo [ERROR] Cannot connect to SQL Server. Check .env settings. & pause & exit /b 1 )

echo [5/9] Validating migration scripts...
set "MIGRATIONS=01_master_loader.py 02_bank_loader.py 03_gl_loader.py 04_document_ingest.py 05_neural_seeder.py 06_verify.py"
set "MISSING=0"
for %%f in (%MIGRATIONS%) do ( if not exist "%MIGRATION_DIR%\%%f" ( echo [ERROR] Missing: %%f & set "MISSING=1" ) )
if "%MISSING%"=="1" ( echo [ERROR] One or more migrations missing. & pause & exit /b 1 )
echo [OK] All 6 scripts found.
if exist "%MIGRATION_DIR%\99_rollback.py" ( echo [OK] Rollback script found. ) else ( echo [WARN] No rollback script. )

echo [6/9] Running DDL schemas...
if exist "%SQL_DIR%\00_Schema_DDL.sql" (
    echo [DDL] Creating schema...
    sqlcmd -S %SQL_SERVER% -d %SQL_DATABASE% -U %SQL_USERNAME% -P %SQL_PASSWORD% -i "%SQL_DIR%\00_Schema_DDL.sql" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 ( echo [WARN] sqlcmd not found or DDL failed. Use app init_db() instead. )
) else ( echo [SKIP] No DDL file found. Run app's init_db() first. )

echo [7/9] Running migrations in order...
set "STEP=0"
for %%f in (%MIGRATIONS%) do (
    set /a "STEP+=1"
    echo [STEP !STEP!/6] Running %%f ...
    python "%MIGRATION_DIR%\%%f" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [FAILED] %%f
        echo [ROLLBACK] Running 99_rollback.py...
        if exist "%MIGRATION_DIR%\99_rollback.py" ( python "%MIGRATION_DIR%\99_rollback.py" --full >> "%LOG_FILE%" 2>&1 )
        echo [ERROR] Migration failed. Review: %LOG_FILE%
        pause & exit /b 1
    )
    echo [OK] %%f completed.
)

echo [8/9] Running integrity verification...
python "%MIGRATION_DIR%\06_verify.py" >> "%LOG_FILE%" 2>&1
echo [OK] Verification complete.

echo [9/9] Migration complete.
echo Finished: %date% %time% >> "%LOG_FILE%"
echo.
echo  ============================================
echo   MIGRATION COMPLETE - Log: %LOG_FILE%
echo  ============================================
pause
