"""PostgreSQL backup engine — pg_dump, compress, verify, restore, retention."""
import os
import shutil
import subprocess
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BACKUP_DIR = Path(__file__).resolve().parent.parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

DB_NAME = os.getenv("SQL_DATABASE", "IHE_ERP")
DB_HOST = os.getenv("SQL_SERVER", "localhost")
DB_USER = os.getenv("SQL_USERNAME", "sa")
DB_PASS = os.getenv("SQL_PASSWORD", "IHE_ERP_2024!")

RETENTION_DAYS = {"daily": 7, "weekly": 28, "monthly": 365}
SCHEDULE = {
    "daily": {"hour": 2, "minute": 0},
    "weekly": {"day": 6, "hour": 3, "minute": 0},
    "monthly": {"day": 1, "hour": 4, "minute": 0},
}


def _use_pg_dump() -> bool:
    return shutil.which("pg_dump") is not None


def _use_sqlcmd() -> bool:
    return shutil.which("sqlcmd") is not None


def create_backup(label: str = "manual") -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    period = datetime.now().strftime("%Y-%m")
    filename = f"ihe_backup_{timestamp}_{label}.bak"
    filepath = BACKUP_DIR / period / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if _use_sqlcmd():
        cmd = [
            "sqlcmd",
            "-S", DB_HOST,
            "-U", DB_USER,
            "-P", DB_PASS,
            "-Q", f"BACKUP DATABASE [{DB_NAME}] TO DISK='{filepath}' WITH INIT, COMPRESSION",
        ]
    else:
        cmd = [
            "pg_dump",
            "-h", DB_HOST,
            "-U", DB_USER,
            "-d", DB_NAME,
            "-F", "c",
            "-f", str(filepath),
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASS
    try:
        if _use_sqlcmd():
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        else:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr, "filename": filename}

    sha256 = _checksum(filepath)
    size_bytes = filepath.stat().st_size
    manifest = {
        "filename": filename,
        "path": str(filepath),
        "timestamp": timestamp,
        "label": label,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "status": "ok",
    }
    manifest_path = filepath.with_suffix(".json")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def list_backups() -> list[dict]:
    backups = []
    for f in sorted(BACKUP_DIR.rglob("*.bak")):
        manifest_path = f.with_suffix(".json")
        if manifest_path.exists():
            backups.append(json.loads(manifest_path.read_text()))
        else:
            backups.append({
                "filename": f.name,
                "path": str(f),
                "timestamp": f.stem.split("_")[1] if "_" in f.stem else "unknown",
                "label": f.stem.split("_")[-1] if "_" in f.stem else "unknown",
                "size_bytes": f.stat().st_size,
                "sha256": "",
                "status": "unverified",
            })
    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)


def verify_backup(filename: str) -> dict:
    backups = list_backups()
    match = [b for b in backups if b["filename"] == filename]
    if not match:
        return {"status": "error", "error": "Backup not found"}
    entry = match[0]
    filepath = Path(entry["path"])
    if not filepath.exists():
        return {"status": "error", "error": "File not found on disk"}
    sha256 = _checksum(filepath)
    expected = entry.get("sha256", "")
    if expected and sha256 != expected:
        return {"status": "error", "error": "Checksum mismatch", "expected": expected, "actual": sha256}
    return {"status": "ok", "filename": filename, "sha256": sha256, "size_bytes": filepath.stat().st_size}


def restore_backup(filename: str) -> dict:
    backups = list_backups()
    match = [b for b in backups if b["filename"] == filename]
    if not match:
        return {"status": "error", "error": "Backup not found"}
    filepath = Path(match[0]["path"])
    if not filepath.exists():
        return {"status": "error", "error": "Backup file not found"}
    verify = verify_backup(filename)
    if verify["status"] != "ok":
        return verify
    if _use_sqlcmd():
        cmd = ["sqlcmd", "-S", DB_HOST, "-U", DB_USER, "-P", DB_PASS,
               "-Q", f"RESTORE DATABASE [{DB_NAME}] FROM DISK='{filepath}' WITH REPLACE"]
    else:
        cmd = ["pg_restore", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME,
               "-c", "--if-exists", str(filepath)]
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASS
    try:
        if _use_sqlcmd():
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        else:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}
    return {"status": "ok", "message": f"Restored from {filename}"}


def cleanup_retention() -> dict:
    removed = []
    errors = []
    for period, days in RETENTION_DAYS.items():
        cutoff = datetime.now() - timedelta(days=days)
        for f in list(BACKUP_DIR.rglob("*.bak")):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                try:
                    f.unlink()
                    j = f.with_suffix(".json")
                    if j.exists():
                        j.unlink()
                    removed.append(str(f.name))
                except Exception as e:
                    errors.append(str(e))
    return {"status": "ok", "removed": removed, "errors": errors, "count": len(removed)}


def get_schedule_config() -> dict:
    return {
        "retention_days": RETENTION_DAYS,
        "schedule": SCHEDULE,
        "backup_dir": str(BACKUP_DIR),
        "engine": "sqlcmd" if _use_sqlcmd() else ("pg_dump" if _use_pg_dump() else "none"),
    }


def _checksum(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
