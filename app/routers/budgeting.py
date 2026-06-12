from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import budgeting_service
from app.schemas.budgeting import (
    BudgetPeriodCreate, BudgetPeriodUpdate, BudgetPeriodResponse,
    BudgetLineCreate, BudgetLineUpdate, BudgetLineResponse, BudgetLineList,
    BudgetCommitmentCreate, BudgetCommitmentResponse,
    BudgetRevisionCreate, BudgetRevisionResponse,
    BudgetVsActualResponse, BudgetVsActualItem,
)

router = APIRouter(prefix="/api/budgeting", tags=["Budgeting"])


@router.get("/periods", response_model=list[BudgetPeriodResponse])
def list_periods(fiscal_year: int | None = Query(None), db: Session = Depends(get_db)):
    return budgeting_service.get_budget_periods(db, fiscal_year=fiscal_year)


@router.get("/periods/{code}", response_model=BudgetPeriodResponse)
def get_period(code: str, db: Session = Depends(get_db)):
    period = budgeting_service.get_budget_period(db, code)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget period not found")
    return period


@router.post("/periods", response_model=BudgetPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_period(data: BudgetPeriodCreate, db: Session = Depends(get_db)):
    return budgeting_service.create_budget_period(db, data)


@router.put("/periods/{code}", response_model=BudgetPeriodResponse)
def update_period(code: str, data: BudgetPeriodUpdate, db: Session = Depends(get_db)):
    period = budgeting_service.update_budget_period(db, code, data)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget period not found")
    return period


@router.delete("/periods/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_period(code: str, db: Session = Depends(get_db)):
    if not budgeting_service.delete_budget_period(db, code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget period not found")


@router.get("/lines", response_model=BudgetLineList)
def list_lines(
    period_code: str | None = Query(None),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = budgeting_service.get_budget_lines(db, period_code=period_code, category=category, skip=skip, limit=page_size)
    return BudgetLineList(items=items, total=total, page=page, page_size=page_size)


@router.get("/lines/{line_id}", response_model=BudgetLineResponse)
def get_line(line_id: int, db: Session = Depends(get_db)):
    line = budgeting_service.get_budget_line(db, line_id)
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget line not found")
    return line


@router.post("/lines", response_model=BudgetLineResponse, status_code=status.HTTP_201_CREATED)
def create_line(data: BudgetLineCreate, db: Session = Depends(get_db)):
    return budgeting_service.create_budget_line(db, data)


@router.put("/lines/{line_id}", response_model=BudgetLineResponse)
def update_line(line_id: int, data: BudgetLineUpdate, db: Session = Depends(get_db)):
    line = budgeting_service.update_budget_line(db, line_id, data)
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget line not found")
    return line


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line(line_id: int, db: Session = Depends(get_db)):
    if not budgeting_service.delete_budget_line(db, line_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget line not found")


@router.post("/commitments", response_model=BudgetCommitmentResponse, status_code=status.HTTP_201_CREATED)
def create_commitment(data: BudgetCommitmentCreate, db: Session = Depends(get_db)):
    return budgeting_service.create_budget_commitment(db, data)


@router.get("/commitments", response_model=list[BudgetCommitmentResponse])
def list_commitments(line_id: int | None = Query(None), db: Session = Depends(get_db)):
    return budgeting_service.get_commitments(db, line_id=line_id)


@router.post("/revisions", response_model=BudgetRevisionResponse, status_code=status.HTTP_201_CREATED)
def create_revision(data: BudgetRevisionCreate, db: Session = Depends(get_db)):
    return budgeting_service.create_budget_revision(db, data)


@router.get("/revisions", response_model=list[BudgetRevisionResponse])
def list_revisions(line_id: int | None = Query(None), db: Session = Depends(get_db)):
    return budgeting_service.get_revisions(db, line_id=line_id)


@router.get("/vs-actual", response_model=BudgetVsActualResponse)
def budget_vs_actual(
    period_code: str | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    items, period, total_budgeted, total_actual, total_committed = budgeting_service.get_budget_vs_actual(
        db, period_code=period_code, category=category,
    )
    return BudgetVsActualResponse(
        period=period,
        items=items,
        total_budgeted=total_budgeted,
        total_actual=total_actual,
        total_committed=total_committed,
        total_variance=total_budgeted - total_actual - total_committed,
    )
