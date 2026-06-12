from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import financial_reports_service as frs
from app.reports import csv_export
from app.reports import period_comparison as pcmp
from app.reports.cash_flow import CashFlowReport
from app.reports import pdf_export

router = APIRouter(prefix="/reports/financial", tags=["Financial Reports v2"])


# ---------------------------------------------------------------------------
# CSV Export endpoints
# ---------------------------------------------------------------------------

@router.get("/api/trial-balance/csv")
def trial_balance_csv(
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = frs.get_trial_balance(db, as_of_date)
    csv = csv_export.trial_balance_csv(data)
    return StreamingResponse(
        iter([csv]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=trial_balance_{data['as_of_date']}.csv"},
    )


@router.get("/api/profit-loss/csv")
def profit_loss_csv(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = frs.get_profit_loss(db, from_date, to_date)
    csv = csv_export.profit_loss_csv(data)
    return StreamingResponse(
        iter([csv]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=profit_loss_{from_date}_to_{to_date}.csv"},
    )


@router.get("/api/balance-sheet/csv")
def balance_sheet_csv(
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = frs.get_balance_sheet(db, as_of_date)
    csv = csv_export.balance_sheet_csv(data)
    return StreamingResponse(
        iter([csv]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=balance_sheet_{data['as_of_date']}.csv"},
    )


@router.get("/api/cash-flow/csv")
def cash_flow_csv(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = frs.get_cash_flow(db, from_date, to_date)
    csv = csv_export.cash_flow_csv(data)
    return StreamingResponse(
        iter([csv]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cash_flow_{from_date}_to_{to_date}.csv"},
    )


# ---------------------------------------------------------------------------
# Cash Flow v2 — full sections (operating + investing + financing)
# ---------------------------------------------------------------------------

@router.get("/api/cash-flow-v2")
def cash_flow_v2(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    report = CashFlowReport(db)
    return report.generate(from_date, to_date)


@router.get("/api/cash-flow-v2/csv")
def cash_flow_v2_csv(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    report = CashFlowReport(db)
    data = report.generate(from_date, to_date)
    csv = csv_export.cash_flow_csv(data)
    return StreamingResponse(
        iter([csv]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cash_flow_v2_{from_date}_to_{to_date}.csv"},
    )


# ---------------------------------------------------------------------------
# Period Comparison endpoints
# ---------------------------------------------------------------------------

@router.get("/api/compare/trial-balance")
def compare_trial_balance(
    as_of_date: date | None = Query(None),
    compare_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return pcmp.compare_trial_balance(db, as_of_date, compare_date)


@router.get("/api/compare/profit-loss")
def compare_profit_loss(
    from_date: date = Query(...),
    to_date: date = Query(...),
    compare_from: date = Query(...),
    compare_to: date = Query(...),
    db: Session = Depends(get_db),
):
    return pcmp.compare_profit_loss(db, from_date, to_date, compare_from, compare_to)


@router.get("/api/compare/balance-sheet")
def compare_balance_sheet(
    as_of_date: date | None = Query(None),
    compare_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return pcmp.compare_balance_sheet(db, as_of_date, compare_date)


@router.get("/api/compare/cash-flow")
def compare_cash_flow(
    from_date: date = Query(...),
    to_date: date = Query(...),
    compare_from: date = Query(...),
    compare_to: date = Query(...),
    db: Session = Depends(get_db),
):
    return pcmp.compare_cash_flow(db, from_date, to_date, compare_from, compare_to)


# ---------------------------------------------------------------------------
# Convenience: period-based comparison (auto-resolves named periods)
# ---------------------------------------------------------------------------

REPORT_TYPES = {
    "trial_balance": pcmp.compare_trial_balance,
    "profit_loss": pcmp.compare_profit_loss,
    "balance_sheet": pcmp.compare_balance_sheet,
    "cash_flow": pcmp.compare_cash_flow,
}


@router.get("/api/compare")
def compare_by_period(
    report_type: str = Query(..., regex="^(trial_balance|profit_loss|balance_sheet|cash_flow)$"),
    period: str = Query("this_month"),
    compare: str = Query("last_month"),
    db: Session = Depends(get_db),
):
    compare_fn = REPORT_TYPES.get(report_type)
    if not compare_fn:
        raise HTTPException(400, detail=f"Unknown report_type: {report_type}")

    cur_from, cur_to = pcmp._resolve_period(period)
    prev_from, prev_to = pcmp._resolve_period(compare)

    if report_type in ("trial_balance", "balance_sheet"):
        if not cur_to:
            raise HTTPException(400, detail=f"Could not resolve period: {period}")
        return compare_fn(db, as_of_date=cur_to, compare_date=prev_to)

    if not all([cur_from, cur_to, prev_from, prev_to]):
        raise HTTPException(400, detail=f"Could not resolve periods: {period}, {compare}")

    if report_type == "cash_flow":
        return compare_fn(db, cur_from, cur_to, prev_from, prev_to)

    return compare_fn(db, cur_from, cur_to, prev_from, prev_to)


# ---------------------------------------------------------------------------
# PDF Export endpoints
# ---------------------------------------------------------------------------

@router.get("/api/trial-balance/pdf")
def trial_balance_pdf(
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = frs.get_trial_balance(db, as_of_date)
    pdf_bytes = pdf_export.trial_balance_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=trial_balance_{data['as_of_date']}.pdf"},
    )


@router.get("/api/profit-loss/pdf")
def profit_loss_pdf(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = frs.get_profit_loss(db, from_date, to_date)
    pdf_bytes = pdf_export.profit_loss_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=profit_loss_{from_date}_to_{to_date}.pdf"},
    )


@router.get("/api/balance-sheet/pdf")
def balance_sheet_pdf(
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = frs.get_balance_sheet(db, as_of_date)
    pdf_bytes = pdf_export.balance_sheet_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=balance_sheet_{data['as_of_date']}.pdf"},
    )


@router.get("/api/cash-flow/pdf")
def cash_flow_pdf(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = frs.get_cash_flow(db, from_date, to_date)
    pdf_bytes = pdf_export.cash_flow_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cash_flow_{from_date}_to_{to_date}.pdf"},
    )


@router.get("/api/cash-flow-v2/pdf")
def cash_flow_v2_pdf(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    report = CashFlowReport(db)
    pdf_bytes = report.to_pdf(from_date, to_date)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cash_flow_v2_{from_date}_to_{to_date}.pdf"},
    )


@router.get("/api/compare/trial-balance/pdf")
def compare_trial_balance_pdf(
    as_of_date: date | None = Query(None),
    compare_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = pcmp.compare_trial_balance(db, as_of_date, compare_date)
    data["report_type"] = "trial_balance"
    pdf_bytes = pdf_export.comparison_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compare_trial_balance.pdf"},
    )


@router.get("/api/compare/profit-loss/pdf")
def compare_profit_loss_pdf(
    from_date: date = Query(...),
    to_date: date = Query(...),
    compare_from: date = Query(...),
    compare_to: date = Query(...),
    db: Session = Depends(get_db),
):
    data = pcmp.compare_profit_loss(db, from_date, to_date, compare_from, compare_to)
    data["report_type"] = "profit_loss"
    pdf_bytes = pdf_export.comparison_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compare_profit_loss.pdf"},
    )


@router.get("/api/compare/balance-sheet/pdf")
def compare_balance_sheet_pdf(
    as_of_date: date | None = Query(None),
    compare_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = pcmp.compare_balance_sheet(db, as_of_date, compare_date)
    data["report_type"] = "balance_sheet"
    pdf_bytes = pdf_export.comparison_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compare_balance_sheet.pdf"},
    )


@router.get("/api/compare/cash-flow/pdf")
def compare_cash_flow_pdf(
    from_date: date = Query(...),
    to_date: date = Query(...),
    compare_from: date = Query(...),
    compare_to: date = Query(...),
    db: Session = Depends(get_db),
):
    data = pcmp.compare_cash_flow(db, from_date, to_date, compare_from, compare_to)
    data["report_type"] = "cash_flow"
    pdf_bytes = pdf_export.comparison_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compare_cash_flow.pdf"},
    )
