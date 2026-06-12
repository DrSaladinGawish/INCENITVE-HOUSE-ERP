import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai.llm_service import llm_service
from app.services.neural.trainer import trainer

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


@router.post("/backup")
def create_backup(db: Session = Depends(get_db)):
    backup_dir = "data/backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ihe_backup_{timestamp}.json"
    filepath = os.path.join(backup_dir, filename)
    try:
        tables = ["PNRMaster", "SalesInvoice", "PurchaseVoucher", "BankTransaction",
                   "Client", "Vendor", "JournalVoucher", "ChartOfAccounts", "ServiceType"]
        backup_data = {"generated_at": datetime.now().isoformat(), "tables": {}}
        for table in tables:
            try:
                rows = db.execute(text(f"SELECT * FROM dbo.{table}")).mappings().all()
                backup_data["tables"][table] = [dict(r) for r in rows]
            except Exception:
                backup_data["tables"][table] = []
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, default=str)
        size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
        return {"status": "ok", "filename": filename, "size_mb": size_mb, "tables": len(tables)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/backups")
def list_backups():
    backup_dir = "data/backups"
    os.makedirs(backup_dir, exist_ok=True)
    backups = []
    for fname in sorted(os.listdir(backup_dir), reverse=True)[:20]:
        fpath = os.path.join(backup_dir, fname)
        if os.path.isfile(fpath):
            size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 2)
            backups.append({
                "filename": fname,
                "size_mb": size_mb,
                "created_at": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                "download_url": f"/api/v1/intelligence/backup/download/{fname}",
            })
    return {"backups": backups}


@router.get("/backup/download/{filename}")
def download_backup(filename: str):
    filepath = os.path.join("data/backups", filename)
    if not os.path.exists(filepath):
        return {"error": "Backup not found"}
    return FileResponse(filepath, media_type="application/json", filename=filename)


@router.get("/audit")
def get_audit_log(db: Session = Depends(get_db)):
    try:
        rows = db.execute(text("SELECT TOP 100 * FROM dbo.AuditTrail ORDER BY CreatedAt DESC")).mappings().all()
        return {"items": [dict(r) for r in rows]}
    except Exception:
        return {"items": []}


@router.post("/ai/assist")
async def ai_assist(data: dict):
    message = data.get("message", "")
    context = {
        "page": data.get("page_context", "unknown"),
        "user": data.get("user", "User"),
        "form_data": data.get("form_data", {})
    }
    result = await llm_service.ask(message, context)
    return result


@router.post("/neural/train/{predictor_name}")
async def train_predictor(predictor_name: str):
    from app.database import SyncSessionLocal
    from app.models import BankTransaction

    db = SyncSessionLocal()
    try:
        txns = db.query(BankTransaction).order_by(BankTransaction.TransactionDate.desc()).limit(100).all()
        historical = [{
            "date": str(t.TransactionDate),
            "net_amount": float(t.Deposit or 0) - float(t.Withdrawal or 0)
        } for t in txns]

        result = trainer.train_cashflow_predictor(historical)
        return result
    finally:
        db.close()


@router.get("/neural/predict/{predictor_name}")
async def predict(predictor_name: str, periods: int = 3):
    if predictor_name == "cashflow":
        predictions = trainer.predict_cashflow(periods)
        return {
            "predictor": predictor_name,
            "periods": periods,
            "forecast": predictions,
            "unit": "EGP",
            "generated_at": datetime.now().isoformat()
        }
    return {"error": f"Unknown predictor: {predictor_name}"}
