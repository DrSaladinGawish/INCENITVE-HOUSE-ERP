from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.budgeting import BudgetPeriod, BudgetLine, BudgetCommitment, BudgetRevision
from app.schemas.budgeting import (
    BudgetPeriodCreate, BudgetPeriodUpdate,
    BudgetLineCreate, BudgetLineUpdate,
    BudgetCommitmentCreate, BudgetRevisionCreate,
    BudgetVsActualItem,
)


def get_budget_periods(db: Session, fiscal_year: int | None = None) -> list[BudgetPeriod]:
    stmt = select(BudgetPeriod).order_by(BudgetPeriod.FiscalYear.desc(), BudgetPeriod.StartDate)
    if fiscal_year:
        stmt = stmt.where(BudgetPeriod.FiscalYear == fiscal_year)
    return list(db.execute(stmt).scalars().all())


def get_budget_period(db: Session, code: str) -> BudgetPeriod | None:
    return db.get(BudgetPeriod, code)


def create_budget_period(db: Session, data: BudgetPeriodCreate) -> BudgetPeriod:
    period = BudgetPeriod(**data.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def update_budget_period(db: Session, code: str, data: BudgetPeriodUpdate) -> BudgetPeriod | None:
    period = db.get(BudgetPeriod, code)
    if not period:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(period, key, val)
    db.commit()
    db.refresh(period)
    return period


def delete_budget_period(db: Session, code: str) -> bool:
    period = db.get(BudgetPeriod, code)
    if not period:
        return False
    db.delete(period)
    db.commit()
    return True


def get_budget_lines(
    db: Session, period_code: str | None = None, category: str | None = None,
    skip: int = 0, limit: int = 50,
) -> tuple[list[BudgetLine], int]:
    stmt = select(BudgetLine).options(joinedload(BudgetLine.budget_period))
    if period_code:
        stmt = stmt.where(BudgetLine.BudgetPeriodCode == period_code)
    if category:
        stmt = stmt.where(BudgetLine.Category == category)
    total = db.execute(select(func.count(BudgetLine.BudgetLineID)).select_from(stmt.subquery())).scalar() or 0
    stmt = stmt.order_by(BudgetLine.BudgetLineID).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().unique().all())
    return items, total


def get_budget_line(db: Session, line_id: int) -> BudgetLine | None:
    stmt = select(BudgetLine).where(BudgetLine.BudgetLineID == line_id).options(
        joinedload(BudgetLine.budget_period), joinedload(BudgetLine.commitments)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def create_budget_line(db: Session, data: BudgetLineCreate) -> BudgetLine:
    line = BudgetLine(**data.model_dump())
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


def update_budget_line(db: Session, line_id: int, data: BudgetLineUpdate) -> BudgetLine | None:
    line = db.get(BudgetLine, line_id)
    if not line:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(line, key, val)
    db.commit()
    db.refresh(line)
    return line


def delete_budget_line(db: Session, line_id: int) -> bool:
    line = db.get(BudgetLine, line_id)
    if not line:
        return False
    db.delete(line)
    db.commit()
    return True


def create_budget_commitment(db: Session, data: BudgetCommitmentCreate) -> BudgetCommitment:
    commit = BudgetCommitment(**data.model_dump())
    total = db.execute(
        select(func.coalesce(func.sum(BudgetCommitment.Amount), 0)).where(
            BudgetCommitment.BudgetLineID == data.BudgetLineID
        )
    ).scalar() or 0
    line = db.get(BudgetLine, data.BudgetLineID)
    if line:
        line.CommittedAmount = float(total) + data.Amount
    db.add(commit)
    db.commit()
    db.refresh(commit)
    return commit


def get_commitments(db: Session, line_id: int | None = None) -> list[BudgetCommitment]:
    stmt = select(BudgetCommitment).order_by(BudgetCommitment.CreatedAt.desc())
    if line_id:
        stmt = stmt.where(BudgetCommitment.BudgetLineID == line_id)
    return list(db.execute(stmt).scalars().all())


def create_budget_revision(db: Session, data: BudgetRevisionCreate) -> BudgetRevision:
    rev = BudgetRevision(**data.model_dump())
    line = db.get(BudgetLine, data.BudgetLineID)
    if line:
        line.BudgetedAmount = data.NewAmount
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return rev


def get_revisions(db: Session, line_id: int | None = None) -> list[BudgetRevision]:
    stmt = select(BudgetRevision).order_by(BudgetRevision.RevisedAt.desc())
    if line_id:
        stmt = stmt.where(BudgetRevision.BudgetLineID == line_id)
    return list(db.execute(stmt).scalars().all())


def get_budget_vs_actual(
    db: Session, period_code: str | None = None, category: str | None = None,
) -> tuple[list[BudgetVsActualItem], BudgetPeriod | None]:
    stmt = select(BudgetLine).options(joinedload(BudgetLine.budget_period))
    if period_code:
        stmt = stmt.where(BudgetLine.BudgetPeriodCode == period_code)
    if category:
        stmt = stmt.where(BudgetLine.Category == category)
    lines = list(db.execute(stmt).scalars().unique().all())

    period = None
    items = []
    total_budgeted = total_actual = total_committed = 0.0
    for line in lines:
        if not period and line.budget_period:
            period = line.budget_period
        bud = float(line.BudgetedAmount or 0)
        act = float(line.ActualAmount or 0)
        com = float(line.CommittedAmount or 0)
        remaining = bud - act - com
        util = ((act + com) / bud * 100) if bud else 0
        items.append(BudgetVsActualItem(
            BudgetLineID=line.BudgetLineID,
            BudgetPeriodCode=line.BudgetPeriodCode,
            Category=line.Category,
            Description=line.Description,
            BudgetedAmount=bud,
            ActualAmount=act,
            CommittedAmount=com,
            RemainingBudget=remaining,
            UtilizationPct=round(util, 2),
        ))
        total_budgeted += bud
        total_actual += act
        total_committed += com
    return items, period, total_budgeted, total_actual, total_committed
