"""
IH-ERP Launcher Router
Provides endpoints for the launcher dashboard and test execution
Mounted at: /api/v1/launcher
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import subprocess
import json
import os
from datetime import datetime

router = APIRouter(prefix="/api/v1/launcher", tags=["Launcher"])

class TestRequest(BaseModel):
    target_url: str = "http://localhost:9001"

class RestartRequest(BaseModel):
    confirm: bool = False


@router.get("/status")
async def launcher_status():
    """Get launcher and system status"""
    return {
        "launcher_version": "2.0.0",
        "ihf_pattern": "v1.0.0",
        "server_time": datetime.now().isoformat(),
        "server_pid": os.getpid(),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "working_directory": os.getcwd(),
        "status": "running"
    }


@router.post("/run-test")
async def run_launcher_test(request: TestRequest, background_tasks: BackgroundTasks):
    """Run the launcher test suite in background"""
    def execute_test():
        try:
            result = subprocess.run(
                ["python", "-m", "app.tests.test_launcher", request.target_url],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.getcwd()
            )
            # Results are saved to reports/launcher_test_*.json
            return result.returncode == 0
        except Exception as e:
            print(f"Test execution error: {e}")
            return False

    background_tasks.add_task(execute_test)

    return {
        "status": "started",
        "message": f"Launcher test suite started against {request.target_url}",
        "report_path": "reports/launcher_test_TIMESTAMP.json"
    }


@router.get("/test-report/latest")
async def get_latest_test_report():
    """Get the most recent test report"""
    reports_dir = os.path.join(os.getcwd(), "reports")
    if not os.path.exists(reports_dir):
        raise HTTPException(status_code=404, detail="No reports directory found")

    reports = [f for f in os.listdir(reports_dir) if f.startswith("launcher_test_") and f.endswith(".json")]
    if not reports:
        raise HTTPException(status_code=404, detail="No test reports found")

    latest = sorted(reports, reverse=True)[0]
    with open(os.path.join(reports_dir, latest), "r") as f:
        data = json.load(f)

    return data


@router.get("/test-reports")
async def list_test_reports():
    """List all available test reports"""
    reports_dir = os.path.join(os.getcwd(), "reports")
    if not os.path.exists(reports_dir):
        return {"reports": []}

    reports = []
    for f in sorted(os.listdir(reports_dir), reverse=True):
        if f.startswith("launcher_test_") and f.endswith(".json"):
            path = os.path.join(reports_dir, f)
            stat = os.stat(path)
            reports.append({
                "filename": f,
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    return {"reports": reports[:20]}  # Last 20


@router.post("/restart")
async def restart_server(request: RestartRequest):
    """Restart the IH-ERP server (requires confirmation)"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")

    def do_restart():
        import time
        time.sleep(2)
        os._exit(0)  # Force restart (supervisor/docker will restart)

    import threading
    threading.Thread(target=do_restart, daemon=True).start()

    return {
        "status": "restarting",
        "message": "Server restart initiated. Will be back in 10 seconds."
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def launcher_dashboard():
    """Serve the launcher dashboard HTML"""
    dashboard_path = os.path.join(os.getcwd(), "app", "templates", "launcher_dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()

    return """
    <!DOCTYPE html>
    <html>
    <head><title>IH-ERP Launcher</title></head>
    <body>
        <h1>IH-ERP Launcher Dashboard</h1>
        <p>Dashboard template not found. Please ensure launcher_dashboard.html exists.</p>
        <p><a href="/api/v1/launcher/status">Check Status</a></p>
    </body>
    </html>
    """


@router.get("/dashboard-v2", response_class=HTMLResponse)
async def dashboard_v2():
    """Part 4 Dashboard v2.0 — System Health & Assessment"""
    dashboard_path = os.path.join(os.getcwd(), "app", "templates", "launcher_dashboard_v2.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content="<h1>Dashboard v2.0 not found</h1>", status_code=404)
