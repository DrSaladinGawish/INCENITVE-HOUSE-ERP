import json, hashlib, io, csv, re, uuid
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/v1/archive", tags=["Archive"])

USB_ROOT = Path("D:/IncentiveHouse_ERP/USB Drive")
REPORTS_DIR = Path("D:/IncentiveHouse_ERP/reports")
ARCHIVE_STRUCTURE = {
    "01_TRANSACTION_DOCUMENTS": ["BANKING", "INVOICES", "PURCHASE_ORDERS", "SALES", "EVENTS", "HR_PAYROLL"],
    "02_MASTER_DATA": ["COA", "ITEMS", "CLIENTS", "SUPPLIERS"],
    "03_AUDIT_TRAIL": ["USER_ACTIONS", "DATA_CHANGES", "SYSTEM_LOGS"],
    "04_BACKUPS": ["DAILY", "WEEKLY", "MONTHLY"],
    "05_REPORTS": ["FINANCIAL", "OPERATIONAL"],
    "06_UNCLASSIFIED": ["REVIEW_QUEUE"],
}

DOC_TYPE_FOLDER_MAP = {
    "invoice": "INVOICES",
    "purchase": "PURCHASE_ORDERS",
    "banking": "BANKING",
    "payment": "BANKING",
    "sales": "SALES",
    "client": "SALES",
    "vendor": "PURCHASE_ORDERS",
    "contract": "EVENTS",
    "payroll": "HR_PAYROLL",
    "tax": "INVOICES",
    "financial": "REPORTS",
    "report": "REPORTS",
    "legal": "EVENTS",
    "photo": "EVENTS",
    "backup": "BACKUPS",
}

TRNX_PREFIXES = {
    "BANKING": "BNK",
    "INVOICES": "INV",
    "PURCHASE_ORDERS": "PO",
    "SALES": "SAL",
    "EVENTS": "EVN",
    "HR_PAYROLL": "HR",
}


def _compute_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def _get_latest_scan() -> dict | None:
    scans = sorted(REPORTS_DIR.glob("usb_scan_*.json"))
    if not scans:
        return None
    with open(scans[-1], encoding="utf-8") as f:
        return json.load(f)


def _auto_sort_folder(doc_type: str, trnx_type: str | None = None) -> str:
    if trnx_type and trnx_type in DOC_TYPE_FOLDER_MAP:
        return DOC_TYPE_FOLDER_MAP[trnx_type]
    return DOC_TYPE_FOLDER_MAP.get(doc_type, "06_UNCLASSIFIED/REVIEW_QUEUE")


def _build_filename(trnx_type: str = "", trnx_number: str = "", entity: str = "", date_str: str = "", desc: str = "") -> str:
    parts = []
    if trnx_type and trnx_type in TRNX_PREFIXES:
        parts.append(TRNX_PREFIXES[trnx_type])
    elif trnx_type:
        parts.append(trnx_type[:3].upper())
    if trnx_number:
        parts.append(trnx_number)
    if entity:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", entity)[:30]
        parts.append(safe.upper())
    if date_str:
        parts.append(date_str.replace("-", ""))
    else:
        parts.append(date.today().strftime("%Y%m%d"))
    if desc:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", desc)[:20]
        parts.append(safe.upper())
    return "_".join(parts)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def archive_status():
    """USB connection status + index stats."""
    connected = USB_ROOT.exists()
    if not connected:
        return {"connected": False, "message": "USB Drive not mounted"}
    files = list(USB_ROOT.rglob("*"))
    file_count = len([f for f in files if f.is_file()])
    scan = _get_latest_scan()
    return {
        "connected": True,
        "total_files": file_count,
        "last_scan": scan["scan_time"] if scan else None,
        "summary": scan["summary"] if scan else None,
    }


@router.post("/scan")
def trigger_scan():
    """Trigger a background full scan — runs synchronously for now."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "usb_archive_scanner.py"],
        capture_output=True, text=True, cwd=USB_ROOT.parent,
    )
    scan = _get_latest_scan()
    return {
        "status": "complete" if result.returncode == 0 else "failed",
        "stdout": result.stdout[-500:],
        "stderr": result.stderr[-500:],
        "scan": scan,
    }


@router.get("/browse")
def browse_archive(
    category: str = Query(None),
    doc_type: str = Query(None),
    entity: str = Query(None),
    trnx: str = Query(None),
):
    """Browse indexed files with filters."""
    scan = _get_latest_scan()
    if not scan:
        raise HTTPException(404, detail="No scan data found. Run scan first.")
    items = scan.get("index", [])
    if category:
        items = [i for i in items if category.lower() in i.get("path", "").lower()]
    if doc_type:
        items = [i for i in items if i.get("type") == doc_type]
    if entity:
        items = [i for i in items if entity.lower() in i.get("path", "").lower()]
    if trnx:
        items = [i for i in items if trnx.lower() in i.get("path", "").lower()]
    return {
        "total": len(items),
        "items": sorted(items, key=lambda x: x.get("path", ""))[:200],
    }


@router.get("/duplicates")
def list_duplicates(min_group: int = Query(2)):
    """List all duplicate file groups from latest scan."""
    scan = _get_latest_scan()
    if not scan:
        raise HTTPException(404, detail="No scan data found")
    dups = scan.get("duplicates", {})
    groups = [(md5, paths) for md5, paths in dups.items() if len(paths) >= min_group]
    groups.sort(key=lambda x: -len(x[1]))
    return {
        "total_groups": len(groups),
        "total_excess": sum(len(g) - 1 for _, g in groups),
        "groups": [
            {"md5": md5, "count": len(paths), "paths": paths, "waste_bytes": sum(
                Path(USB_ROOT / p).stat().st_size for p in paths[1:]
            ) if len(paths) > 1 else 0}
            for md5, paths in groups[:100]
        ],
    }


@router.post("/dedup")
def deduplicate(md5: str = Query(...), keep_path: str = Query(None)):
    """Mark a duplicate group — keeps one copy, marks others as duplicate."""
    scan = _get_latest_scan()
    if not scan:
        raise HTTPException(404, detail="No scan data found")
    dups = scan.get("duplicates", {})
    if md5 not in dups:
        raise HTTPException(404, detail="MD5 not found in duplicate groups")
    paths = dups[md5]
    if keep_path and keep_path in paths:
        primary = keep_path
    else:
        primary = paths[0]
    return {
        "status": "dedup_planned",
        "md5": md5,
        "primary": primary,
        "duplicates": [p for p in paths if p != primary],
        "recovered_bytes": sum(
            Path(USB_ROOT / p).stat().st_size for p in paths if p != primary
        ),
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form("06_UNCLASSIFIED"),
    doc_type: str = Form("unclassified"),
    trnx_type: str = Form(""),
    trnx_number: str = Form(""),
    entity: str = Form(""),
    desc: str = Form(""),
):
    """Upload file with auto-sort naming and folder placement."""
    content = await file.read()
    md5 = _compute_md5(content)

    # Check for duplicates
    scan = _get_latest_scan()
    if scan:
        for entry in scan.get("index", []):
            if entry.get("md5") == md5:
                return {"status": "duplicate", "message": "File already exists in archive", "existing_path": entry["path"]}

    folder = _auto_sort_folder(doc_type, trnx_type)
    target_dir = USB_ROOT / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = _build_filename(trnx_type, trnx_number, entity, date.today().isoformat(), desc)
    ext = Path(file.filename).suffix if file.filename else ""
    target_path = target_dir / f"{filename}{ext}"

    # Avoid overwrites
    counter = 1
    while target_path.exists():
        target_path = target_dir / f"{filename}_{counter}{ext}"
        counter += 1

    with open(target_path, "wb") as f:
        f.write(content)

    return {
        "status": "uploaded",
        "path": str(target_path.relative_to(USB_ROOT)),
        "size": len(content),
        "md5": md5,
    }


@router.get("/download/{file_uuid:path}")
def download_file(file_uuid: str):
    """Download a file by UUID or relative path."""
    scan = _get_latest_scan()
    if not scan:
        raise HTTPException(404, detail="No scan data found")

    for entry in scan.get("index", []):
        if entry.get("path") == file_uuid or entry.get("path", "").endswith(file_uuid):
            full_path = USB_ROOT / entry["path"]
            if full_path.exists():
                return FileResponse(str(full_path), filename=Path(entry["path"]).name)
    raise HTTPException(404, detail="File not found")


@router.post("/link-to-transaction")
def link_to_transaction(
    file_path: str = Query(...),
    trnx_type: str = Query(...),
    trnx_number: str = Query(...),
    db: Session = Depends(get_db),
):
    """Link an archived file to a business transaction in the DB."""
    full_path = USB_ROOT / file_path
    if not full_path.exists():
        raise HTTPException(404, detail="File not found on disk")

    # Check DB link table exists
    try:
        db.execute(text("SELECT TOP 1 1 FROM dbo.transaction_documents"))
        table_exists = True
    except Exception:
        table_exists = False

    result = {
        "status": "linked",
        "trnx_type": trnx_type,
        "trnx_number": trnx_number,
        "file": file_path,
        "db_table": table_exists,
    }

    if table_exists:
        try:
            md5 = _compute_md5(open(full_path, "rb").read())
            db.execute(
                text("""
                    IF NOT EXISTS (SELECT 1 FROM dbo.transaction_documents td
                        JOIN dbo.usb_archive_index f ON td.FileID = f.FileID
                        WHERE f.MD5Hash = :md5 AND td.TRNXNumber = :trnx)
                    BEGIN
                        DECLARE @fid INT;
                        SELECT @fid = FileID FROM dbo.usb_archive_index WHERE MD5Hash = :md5;
                        IF @fid IS NULL
                        BEGIN
                            INSERT INTO dbo.usb_archive_index (FilePath, FileName, FileExtension, FileSize, MD5Hash, DocumentType, TRNXNumber, TRNXType)
                            VALUES (:path, :name, :ext, :size, :md5, :type, :trnx, :trnx_type);
                            SET @fid = SCOPE_IDENTITY();
                        END
                        INSERT INTO dbo.transaction_documents (FileID, TRNXType, TRNXNumber) VALUES (@fid, :trnx_type, :trnx);
                    END
                """),
                {
                    "md5": md5,
                    "path": file_path,
                    "name": Path(file_path).name,
                    "ext": Path(file_path).suffix,
                    "size": full_path.stat().st_size,
                    "type": "linked",
                    "trnx": trnx_number,
                    "trnx_type": trnx_type,
                },
            )
            db.commit()
            result["db_linked"] = True
        except Exception as e:
            result["db_linked"] = False
            result["db_error"] = str(e)

    return result


@router.get("/transaction/{trnx_type}/{trnx_number}")
def get_transaction_documents(trnx_type: str, trnx_number: str, db: Session = Depends(get_db)):
    """Get all archived files linked to a specific transaction."""
    try:
        rows = db.execute(
            text("SELECT * FROM dbo.vw_transaction_documents WHERE TRNXType = :type AND TRNXNumber = :num ORDER BY LinkedAt DESC"),
            {"type": trnx_type.upper(), "num": trnx_number},
        ).fetchall()
        docs = [dict(r._mapping) for r in rows]
        return {"trnx_type": trnx_type, "trnx_number": trnx_number, "documents": docs}
    except Exception as e:
        return {"trnx_type": trnx_type, "trnx_number": trnx_number, "error": str(e), "documents": []}
