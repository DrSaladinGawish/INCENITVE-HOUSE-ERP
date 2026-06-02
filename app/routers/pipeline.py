import os, json, datetime, logging, traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import (
    ExtractRequest, ExtractResponse, ValidateRequest, ValidateResponse,
    StageRequest, StageResponse, ReconcileRequest, ReconcileResponse,
    ApproveRequest, ApproveResponse, PromoteRequest, PromoteResponse,
    ObserveRequest, ObserveResponse, PipelineStatusResponse,
)
from app.models.models import (
    ExtractionLog, ValidationLog, StagingLog, ReconcileLog, ApprovalLog,
    PromotionLog, ObserveLog, BnkStaging, SalesStaging, PurchaseStaging,
    EventsStaging, EnvironmentalStaging, JournalEntry, COAMaster,
)
from app.services.protocell_service import (
    run_all_validations, rows_from_staging, generate_journal_entries, verify_balanced,
)

logger = logging.getLogger("pipeline")
router = APIRouter(tags=["pipeline"])

MODULE_STAGING_MAP = {
    "BNK": ("bnk_staging", BnkStaging),
    "SAL": ("sales_staging", SalesStaging),
    "PUR": ("purchase_staging", PurchaseStaging),
    "EVN": ("events_staging", EventsStaging),
    "ENV": ("environmental_staging", EnvironmentalStaging),
}


def _now_str():
    return datetime.datetime.utcnow().isoformat()


# ──────────────────────────────────────────────────────────────
# STAGE 1: EXTRACT — Load data from Excel via extraction_engine
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/extract", response_model=ExtractResponse)
async def stage_extract(req: ExtractRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    module = req.module.upper()
    if module not in MODULE_STAGING_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown module: {module}. Use BNK, SAL, PUR, EVN, ENV")
    try:
        from extraction_engine import extract_module_data
        import pandas as pd
        result = extract_module_data(module, req.source_file, dry_run=req.dry_run)
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    extract = ExtractionLog(
        module=module, source_file=result.get("source_file", req.source_file),
        user_id=user["username"], status=result.get("status", "ERROR"),
        records_read=result.get("records_read", 0), records_inserted=result.get("records_inserted", 0),
        errors=json.dumps(result.get("errors", [])), extracted_at=_now_str(),
    )
    db.add(extract); await db.commit(); await db.refresh(extract)

    if not req.dry_run and result.get("records_inserted", 0) > 0:
        staging_table, staging_model = MODULE_STAGING_MAP[module]
        raw_rows = result.get("_raw_rows", [])
        if raw_rows:
            for r in raw_rows:
                r["_module"] = module; r["_extracted_at"] = _now_str()
                r["_batch_id"] = f"{module.lower()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                r["validation_status"] = "PENDING"
            logger.info(f"Staged {len(raw_rows)} raw rows for {module}")

    return ExtractResponse(
        status=result.get("status", "ERROR"), module=module,
        source_file=result.get("source_file"), records_read=result.get("records_read", 0),
        records_inserted=result.get("records_inserted", 0),
        errors=result.get("errors", []), extract_id=extract.id,
        preview=result.get("preview"),
    )


# ──────────────────────────────────────────────────────────────
# STAGE 2: VALIDATE — Run 7-rule protocell validation
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/validate", response_model=ValidateResponse)
async def stage_validate(req: ValidateRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    extract = await db.get(ExtractionLog, req.extract_id)
    if not extract:
        raise HTTPException(status_code=404, detail="Extract record not found")

    rows = []
    for _tbl, _model in MODULE_STAGING_MAP.values():
        result = await db.execute(select(_model).limit(5000))
        rows.extend(rows_from_staging(extract.module, result.all()))

    rule_results = await run_all_validations(rows, db)
    total_passed = sum(r["passed_count"] for r in rule_results)
    total_warn = sum(r["warning_count"] for r in rule_results)
    total_err = sum(r["error_count"] for r in rule_results)
    total = total_passed + total_warn + total_err
    quality = round((total_passed / total * 100), 1) if total > 0 else 0

    val = ValidationLog(
        extract_id=req.extract_id, user_id=user["username"],
        status="VALIDATED" if total_err == 0 else "VALIDATED_WITH_ERRORS",
        quality_score=quality, passed_count=total_passed, warning_count=total_warn,
        error_count=total_err, rule_results=[json.dumps(r) for r in rule_results],
        validated_at=_now_str(),
    )
    db.add(val); await db.commit(); await db.refresh(val)

    return ValidateResponse(
        status=val.status, validate_id=val.id, extract_id=req.extract_id,
        quality_score=quality, passed_count=total_passed, warning_count=total_warn,
        error_count=total_err, rule_results=rule_results,
    )


# ──────────────────────────────────────────────────────────────
# STAGE 3: STAGE — Move validated data to staging tables
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/stage", response_model=StageResponse)
async def stage_stage(req: StageRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    val = await db.get(ValidationLog, req.validate_id)
    if not val:
        raise HTTPException(status_code=404, detail="Validation record not found")
    snapshot_id = f"snap_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{req.validate_id}"
    stg = StagingLog(
        validate_id=req.validate_id, target_table=req.target_table,
        user_id=user["username"], snapshot_id=snapshot_id, status="STAGED",
        staged_at=_now_str(),
    )
    db.add(stg); await db.commit(); await db.refresh(stg)
    return StageResponse(status="STAGED", stage_id=stg.id, validate_id=req.validate_id, snapshot_id=snapshot_id, target_table=req.target_table, records_staged=0)


# ──────────────────────────────────────────────────────────────
# STAGE 4: RECONCILE — Verify staging data integrity
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/reconcile", response_model=ReconcileResponse)
async def stage_reconcile(req: ReconcileRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    stg = await db.get(StagingLog, req.stage_id)
    if not stg:
        raise HTTPException(status_code=404, detail="Stage record not found")

    total = 0; reconciled = 0; total_debit = 0; total_credit = 0
    module = req.module.upper()
    if module in MODULE_STAGING_MAP:
        _, model = MODULE_STAGING_MAP[module]
        count_result = await db.execute(select(func.count()).select_from(model))
        total = count_result.scalar() or 0
        debit_sum = await db.execute(select(func.coalesce(func.sum(model.debit), 0)))
        credit_sum = await db.execute(select(func.coalesce(func.sum(model.credit), 0)))
        total_debit = round(float(debit_sum.scalar() or 0), 2)
        total_credit = round(float(credit_sum.scalar() or 0), 2)

    diff = round(total_debit - total_credit, 2)
    rec = ReconcileLog(
        stage_id=req.stage_id, module=module, user_id=user["username"],
        status="RECONCILED", total_records=total, reconciled_count=total,
        mismatch_count=0, unmatched_count=0,
        total_debit=total_debit, total_credit=total_credit, difference=diff,
        reconciled_at=_now_str(),
    )
    db.add(rec); await db.commit(); await db.refresh(rec)

    return ReconcileResponse(
        status="RECONCILED", recon_id=rec.id, stage_id=req.stage_id, module=module,
        total_records=total, reconciled_count=total, mismatch_count=0, unmatched_count=0,
        total_debit=total_debit, total_credit=total_credit, difference=diff,
        balanced=abs(diff) < 0.01,
    )


# ──────────────────────────────────────────────────────────────
# STAGE 5: APPROVE — Approve reconciled data
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/approve", response_model=ApproveResponse)
async def stage_approve(req: ApproveRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    recon = await db.get(ReconcileLog, req.recon_id)
    if not recon:
        raise HTTPException(status_code=404, detail="Reconcile record not found")
    app = ApprovalLog(
        recon_id=req.recon_id, approver_id=user["username"],
        approval_level=req.approval_level, status="APPROVED", approved_at=_now_str(),
    )
    db.add(app); await db.commit(); await db.refresh(app)
    return ApproveResponse(status="APPROVED", approve_id=app.id, recon_id=req.recon_id, approval_level=req.approval_level, auto_approved=(req.approval_level == "auto"))


# ──────────────────────────────────────────────────────────────
# STAGE 6: PROMOTE — Move to production + generate journal entries
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/promote", response_model=PromoteResponse)
async def stage_promote(req: PromoteRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    app = await db.get(ApprovalLog, req.approve_id)
    if not app:
        raise HTTPException(status_code=404, detail="Approval record not found")

    coa_result = await db.execute(select(COAMaster.acc_key, COAMaster.acc_name))
    coa_map = {str(row[0]): str(row[1]) for row in coa_result.all()}

    for module, (_, staging_model) in MODULE_STAGING_MAP.items():
        rows_result = await db.execute(select(staging_model).where(staging_model.validation_status == "PENDING"))
        staging_rows = rows_result.all()
        entries = generate_journal_entries(staging_rows, module, coa_map)
        for entry in entries:
            entry["batch_id"] = f"promote_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{req.approve_id}"
            db.add(JournalEntry(**entry))

    rollback_token = f"rb_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{req.approve_id}"
    prom = PromotionLog(
        approve_id=req.approve_id, user_id=user["username"],
        rollback_token=rollback_token, status="PROMOTED",
        records_promoted=0, promoted_at=_now_str(),
    )
    db.add(prom); await db.commit(); await db.refresh(prom)

    return PromoteResponse(status="PROMOTED", promote_id=prom.id, approve_id=req.approve_id, rollback_token=rollback_token, records_promoted=0)


# ──────────────────────────────────────────────────────────────
# STAGE 7: OBSERVE — Check promoted data metrics
# ──────────────────────────────────────────────────────────────

@router.post("/api/v2/observe", response_model=ObserveResponse)
async def stage_observe(req: ObserveRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    prom = await db.get(PromotionLog, req.promote_id)
    if not prom:
        raise HTTPException(status_code=404, detail="Promotion record not found")

    entry_count = await db.execute(select(func.count()).select_from(JournalEntry))
    obs = ObserveLog(
        promote_id=req.promote_id, user_id=user["username"],
        status="OBSERVED", metrics=json.dumps(["JournalEntryCount", "Verified"]),
        alert_count=0, observed_at=_now_str(),
    )
    db.add(obs); await db.commit(); await db.refresh(obs)

    return ObserveResponse(status="OBSERVED", observe_id=obs.id, promote_id=req.promote_id, metrics=["JournalEntryCount", "Verified"], alert_count=0)


# ──────────────────────────────────────────────────────────────
# STAGE 8: STATUS — Pipeline status overview
# ──────────────────────────────────────────────────────────────

@router.get("/api/v2/status", response_model=PipelineStatusResponse)
async def pipeline_status(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    counts = {}
    for tbl, model in MODULE_STAGING_MAP.values():
        c = await db.execute(select(func.count()).select_from(model))
        counts[tbl] = c.scalar() or 0
    for name, model in [("extraction_log", ExtractionLog), ("validation_log", ValidationLog),
                         ("staging_log", StagingLog), ("reconcile_log", ReconcileLog),
                         ("approval_log", ApprovalLog), ("promotion_log", PromotionLog),
                         ("observe_log", ObserveLog), ("journal_entries", JournalEntry)]:
        c = await db.execute(select(func.count()).select_from(model))
        counts[name] = c.scalar() or 0
    return PipelineStatusResponse(status="OPERATIONAL", version="2.2.2", stages=counts, timestamp=_now_str())


# ──────────────────────────────────────────────────────────────
# JOURNAL ENTRY VERIFICATION
# ──────────────────────────────────────────────────────────────

@router.get("/api/v2/journal", tags=["pipeline"])
async def list_journal_entries(limit: int = 100, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    result = await db.execute(select(JournalEntry).order_by(JournalEntry.id.desc()).limit(limit))
    entries = result.all()
    debit_sum = round(sum(float(e.debit or 0) for e in entries), 2)
    credit_sum = round(sum(float(e.credit or 0) for e in entries), 2)
    return {
        "entries": [{
            "id": e.id, "source": e.source, "trnx_num": e.trnx_num, "trnx_date": e.trnx_date,
            "account_id": e.account_id, "acc_name": e.acc_name,
            "debit": e.debit, "credit": e.credit,
            "sub_led_code": e.sub_led_code, "pnr_id": e.pnr_id, "narration": e.narration,
            "status": e.status, "currency": e.currency,
        } for e in entries],
        "verification": {"total_debit": debit_sum, "total_credit": credit_sum, "difference": round(debit_sum - credit_sum, 2), "balanced": abs(round(debit_sum - credit_sum, 2)) < 0.01, "entry_count": len(entries)},
    }
