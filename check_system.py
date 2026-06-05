#!/usr/bin/env python3
"""
IHE-ERP System Health Check
Run this on your local machine to verify P1-P7 installation
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(r"D:\IncentiveHouse_ERP")

def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    icon = "OK" if condition else "XX"
    print(f"  [{icon}]  {label}")
    if detail and not condition:
        print(f"       -> {detail}")
    return condition

def run_cmd(cmd, cwd=None, timeout=60):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)

print("=" * 60)
print("  IHE-ERP SYSTEM HEALTH CHECK")
print("=" * 60)

# 1. Directory Structure
print("\n1. DIRECTORY STRUCTURE")
all_ok = True
for subdir in ["app", "app/routers", "app/neural/models", "app/middleware",
               "migrations", "scripts", "tests", ".github/workflows"]:
    path = BASE_DIR / subdir.replace("/", "\\")
    all_ok &= check(f"{subdir}/ exists", path.exists(), f"Missing: {path}")

# 2. Key Files
print("\n2. KEY FILES")
key_files = [
    "app/main.py", "app/db_safe.py", "app/database.py", "app/logging_config.py",
    "app/routers/dashboard_router.py", "app/routers/neural_live.py",
    "app/neural/models/cashflow.py", "app/neural/models/registry.py",
    "app/middleware/request_id.py",
    "Dockerfile", "docker-compose.yml", "nginx.conf",
    "migrations/01_master_loader.py", "migrations/99_rollback.py",
    ".github/workflows/ci.yml",
    "DEPLOYMENT.md", ".env.template"
]
for f in key_files:
    path = BASE_DIR / f.replace("/", "\\")
    check(f"{f}", path.exists(), f"Missing: {path}")

# 3. Python Environment
print("\n3. PYTHON ENVIRONMENT")
py_ok, py_out, _ = run_cmd("python --version")
check("Python 3.11+", py_ok and ("3.11" in py_out or "3.12" in py_out or "3.13" in py_out), py_out.strip())

for pkg in ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "pyodbc",
            "jinja2", "pandas", "scikit-learn", "numpy"]:
    ok, _, _ = run_cmd(f'python -c "import {pkg}"')
    check(f"Package: {pkg}", ok, f"pip install {pkg}")

# 4. ODBC Driver
print("\n4. ODBC DRIVER")
ok, out, err = run_cmd('python -c "import pyodbc; print(pyodbc.drivers())"')
has_driver = ok and ("ODBC Driver 18" in out or "ODBC Driver 17" in out)
check("ODBC Driver 17/18 installed", has_driver, out.strip() if ok else err)

# 5. SQL Server Connection
print("\n5. SQL SERVER CONNECTION")
env_path = BASE_DIR / ".env"
has_env = env_path.exists()
check(".env file exists", has_env, "Copy .env.template -> .env and edit")

if has_env:
    ok, out, err = run_cmd('python -c "from app.config import settings; import pyodbc; conn=pyodbc.connect(settings.SYNC_DATABASE_URL, timeout=5); print(\'CONNECTED\'); conn.close()"', timeout=15)
    connected = ok and "CONNECTED" in out
    check("SQL Server reachable", connected, out.strip() if ok else err)
else:
    check("SQL Server reachable", False, "No .env file")

# 6. Tests
print("\n6. TEST SUITE")
tests_ok, tests_out, _ = run_cmd("python -m pytest tests/ -v --tb=short", cwd=BASE_DIR, timeout=120)
if tests_ok:
    passed = tests_out.count(" passed")
    skipped = tests_out.count(" skipped")
    failed = tests_out.count(" failed")
    check(f"Tests: {passed} passed, {skipped} skipped, {failed} failed", failed == 0, "")
else:
    check("Tests run successfully", False, "pytest not found or tests folder missing")

# 7. Docker
print("\n7. DOCKER")
docker_ok, _, _ = run_cmd("docker --version")
check("Docker installed", docker_ok, "Install Docker Desktop")
if docker_ok:
    compose_ok, _, _ = run_cmd("docker compose version")
    check("Docker Compose available", compose_ok, "Update Docker Desktop")

# 8. Git
print("\n8. VERSION CONTROL")
git_ok, git_out, _ = run_cmd("git -C D:\\IncentiveHouse_ERP status --short")
check("Git initialized", git_ok, "Run: git init")
if git_ok:
    has_changes = len(git_out.strip()) > 0
    check("Working tree clean", not has_changes, f"{len(git_out.strip().splitlines())} uncommitted changes")

# 9. Server Status
print("\n9. SERVER STATUS")
try:
    import urllib.request
    with urllib.request.urlopen("http://localhost:9001/health", timeout=3) as resp:
        check("Server on port 9001", resp.status == 200, f"Status: {resp.status}")
except Exception as e:
    check("Server on port 9001", False, str(e))

# Summary
print("\n" + "=" * 60)
print("  HEALTH CHECK COMPLETE")
print("=" * 60)
print("""
Next steps based on results:
  FAIL SQL Server  -> Deploy migration package to target host
  FAIL Tests       -> Review test output, fix regressions
  FAIL Missing files -> Re-run session deliverables
  All PASS         -> Ready for production deployment
""")
