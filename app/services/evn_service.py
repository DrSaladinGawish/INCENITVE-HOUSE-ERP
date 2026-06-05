from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.ihe_models import PNRMaster, PNRBudgetLineItem, ServiceMainCategory, ServiceSubCategory, ServiceType
from app.schemas.evn import PNRMasterCreate, PNRMasterUpdate, PNRBudgetLineItemCreate


def get_pnrs(
    db: Session,
    year: int | None = None,
    status: str | None = None,
    client_code: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[PNRMaster], int]:
    stmt = select(PNRMaster)
    count_stmt = select(func.count(PNRMaster.PNRNumber))
    if year:
        stmt = stmt.where(PNRMaster.Year == year)
        count_stmt = count_stmt.where(PNRMaster.Year == year)
    if status:
        stmt = stmt.where(PNRMaster.Status == status)
        count_stmt = count_stmt.where(PNRMaster.Status == status)
    if client_code:
        stmt = stmt.where(PNRMaster.ClientCode == client_code)
        count_stmt = count_stmt.where(PNRMaster.ClientCode == client_code)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(PNRMaster.Year.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def get_pnr(db: Session, pnr_number: str) -> PNRMaster | None:
    return db.get(PNRMaster, pnr_number)


def create_pnr(db: Session, data: PNRMasterCreate) -> PNRMaster:
    pnr = PNRMaster(**data.model_dump())
    db.add(pnr)
    db.commit()
    db.refresh(pnr)
    return pnr


def update_pnr(db: Session, pnr_number: str, data: PNRMasterUpdate) -> PNRMaster | None:
    pnr = db.get(PNRMaster, pnr_number)
    if not pnr:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(pnr, key, val)
    db.commit()
    db.refresh(pnr)
    return pnr


def delete_pnr(db: Session, pnr_number: str) -> bool:
    pnr = db.get(PNRMaster, pnr_number)
    if not pnr:
        return False
    db.delete(pnr)
    db.commit()
    return True


def get_budget_line_items(
    db: Session,
    pnr_number: str | None = None,
    skip: int = 0,
    limit: int = 200,
) -> tuple[list[PNRBudgetLineItem], int]:
    stmt = select(PNRBudgetLineItem)
    count_stmt = select(func.count(PNRBudgetLineItem.LineItemID))
    if pnr_number:
        stmt = stmt.where(PNRBudgetLineItem.JobFolder == pnr_number)
        count_stmt = count_stmt.where(PNRBudgetLineItem.JobFolder == pnr_number)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def create_budget_line_item(db: Session, data: PNRBudgetLineItemCreate) -> PNRBudgetLineItem:
    item = PNRBudgetLineItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_service_categories(db: Session) -> list[ServiceMainCategory]:
    stmt = select(ServiceMainCategory).order_by(ServiceMainCategory.DisplayOrder)
    return list(db.execute(stmt).scalars().all())


def get_service_sub_categories(db: Session, main_code: str | None = None) -> list[ServiceSubCategory]:
    stmt = select(ServiceSubCategory)
    if main_code:
        stmt = stmt.where(ServiceSubCategory.MainCategoryCode == main_code)
    return list(db.execute(stmt).scalars().all())


def get_service_types(db: Session, sub_code: str | None = None) -> list[ServiceType]:
    stmt = select(ServiceType)
    if sub_code:
        stmt = stmt.where(ServiceType.SubCategoryCode == sub_code)
    return list(db.execute(stmt).scalars().all())
