"""Backup management router — create, list, verify, restore, cleanup."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from app.auth import get_current_user
from app.services import backup_service

router = APIRouter(prefix="/api/v1/admin/backup", tags=["Backup"])


@router.post("/create")
def create_backup(
    label: str = Query("manual", description="Backup label"),
    current_user: dict = Depends(get_current_user),
):
    result = backup_service.create_backup(label=label)
    if result.get("status") == "error":
        raise HTTPException(500, detail=result["error"])
    return result


@router.get("/list")
def list_backups(current_user: dict = Depends(get_current_user)):
    return backup_service.list_backups()


@router.get("/verify")
def verify_backup(
    filename: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    result = backup_service.verify_backup(filename)
    if result.get("status") == "error":
        raise HTTPException(400, detail=result["error"])
    return result


@router.post("/restore")
def restore_backup(
    filename: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, detail="Admin role required")
    result = backup_service.restore_backup(filename)
    if result.get("status") == "error":
        raise HTTPException(500, detail=result["error"])
    return result


@router.post("/cleanup")
def cleanup_backups(current_user: dict = Depends(get_current_user)):
    return backup_service.cleanup_retention()


@router.get("/download")
def download_backup(
    filename: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    backups = backup_service.list_backups()
    match = [b for b in backups if b["filename"] == filename]
    if not match:
        raise HTTPException(404, detail="Backup not found")
    filepath = match[0]["path"]
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/schedule")
def get_schedule(current_user: dict = Depends(get_current_user)):
    return backup_service.get_schedule_config()


@router.get("/status")
def backup_status(current_user: dict = Depends(get_current_user)):
    backups = backup_service.list_backups()
    latest = backups[0] if backups else None
    total_size = sum(b.get("size_bytes", 0) for b in backups)
    return {
        "total_backups": len(backups),
        "total_size_bytes": total_size,
        "latest_backup": latest,
        "schedule": backup_service.get_schedule_config(),
    }
