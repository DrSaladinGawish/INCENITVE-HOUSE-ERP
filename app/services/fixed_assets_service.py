from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.fixed_assets import Asset, AssetCategory, Depreciation, AssetDisposal
from app.schemas.fixed_assets import (
    AssetCategoryCreate, AssetCategoryUpdate,
    AssetCreate, AssetUpdate, DepreciationCreate, AssetDisposalCreate,
    DepreciationScheduleResponse, DepreciationScheduleItem,
)


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> list[AssetCategory]:
    stmt = select(AssetCategory).order_by(AssetCategory.CategoryCode).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_category(db: Session, category_id: int) -> AssetCategory | None:
    return db.get(AssetCategory, category_id)


def create_category(db: Session, data: AssetCategoryCreate) -> AssetCategory:
    cat = AssetCategory(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, category_id: int, data: AssetCategoryUpdate) -> AssetCategory | None:
    cat = db.get(AssetCategory, category_id)
    if not cat:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(cat, key, val)
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, category_id: int) -> bool:
    cat = db.get(AssetCategory, category_id)
    if not cat:
        return False
    db.delete(cat)
    db.commit()
    return True


def get_assets(
    db: Session,
    category_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Asset], int]:
    stmt = select(Asset)
    count_stmt = select(func.count(Asset.AssetID))
    if category_id:
        stmt = stmt.where(Asset.CategoryID == category_id)
        count_stmt = count_stmt.where(Asset.CategoryID == category_id)
    if status:
        stmt = stmt.where(Asset.Status == status)
        count_stmt = count_stmt.where(Asset.Status == status)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.options(joinedload(Asset.category)).order_by(Asset.AssetCode).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().unique().all())
    return items, total


def get_asset(db: Session, asset_id: int) -> Asset | None:
    stmt = (
        select(Asset)
        .where(Asset.AssetID == asset_id)
        .options(joinedload(Asset.category), joinedload(Asset.depreciation_entries))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def create_asset(db: Session, data: AssetCreate) -> Asset:
    payload = data.model_dump()
    cost = payload["PurchaseCost"]
    salvage = payload.get("SalvageValue", 0)
    life = payload["UsefulLifeYears"]
    payload["CurrentBookValue"] = cost
    payload["AccumulatedDepreciation"] = 0
    payload["Status"] = "Active"
    asset = Asset(**payload)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset_id: int, data: AssetUpdate) -> Asset | None:
    asset = db.get(Asset, asset_id)
    if not asset:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(asset, key, val)
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset_id: int) -> bool:
    asset = db.get(Asset, asset_id)
    if not asset:
        return False
    db.delete(asset)
    db.commit()
    return True


def _straight_line_depreciation(cost: float, salvage: float, life_years: int) -> float:
    if life_years <= 0:
        return 0
    return round((cost - salvage) / life_years, 2)


def compute_depreciation_schedule(asset: Asset) -> DepreciationScheduleResponse:
    annual = _straight_line_depreciation(
        float(asset.PurchaseCost), float(asset.SalvageValue), asset.UsefulLifeYears
    )
    monthly = round(annual / 12, 2)
    schedule: list[DepreciationScheduleItem] = []
    accum = 0.0
    for i in range(asset.UsefulLifeYears * 12):
        period = asset.PurchaseDate + relativedelta(months=i + 1)
        if period > date.today():
            break
        accum = round(accum + monthly, 2)
        book = round(float(asset.PurchaseCost) - accum, 2)
        if book < float(asset.SalvageValue):
            break
        schedule.append(DepreciationScheduleItem(
            PeriodDate=period,
            DepreciationAmount=monthly,
            AccumulatedDepreciation=accum,
            BookValue=book,
        ))
    return DepreciationScheduleResponse(
        AssetID=asset.AssetID,
        AssetCode=asset.AssetCode,
        AssetName=asset.AssetName,
        PurchaseCost=float(asset.PurchaseCost),
        SalvageValue=float(asset.SalvageValue),
        UsefulLifeYears=asset.UsefulLifeYears,
        AnnualDepreciation=annual,
        MonthlyDepreciation=monthly,
        Schedule=schedule,
    )


def get_depreciation_entries(db: Session, asset_id: int) -> list[Depreciation]:
    stmt = select(Depreciation).where(Depreciation.AssetID == asset_id).order_by(Depreciation.PeriodDate)
    return list(db.execute(stmt).scalars().all())


def post_depreciation(db: Session, data: DepreciationCreate) -> Depreciation:
    asset = db.get(Asset, data.AssetID)
    if not asset:
        raise ValueError("Asset not found")
    dep = Depreciation(**data.model_dump())
    dep.IsPosted = True
    dep.PostedAt = datetime.now()
    dep_amount = float(data.DepreciationAmount)
    prev_accum = float(asset.AccumulatedDepreciation)
    new_accum = round(prev_accum + dep_amount, 2)
    asset.AccumulatedDepreciation = new_accum
    asset.CurrentBookValue = round(float(asset.PurchaseCost) - new_accum, 2)
    dep.RunningBookValue = asset.CurrentBookValue
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def dispose_asset(db: Session, asset_id: int, data: AssetDisposalCreate) -> AssetDisposal:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise ValueError("Asset not found")
    if asset.Status == "Disposed":
        raise ValueError("Asset already disposed")
    book_value = float(asset.CurrentBookValue)
    proceeds = data.DisposalProceeds
    cost = data.DisposalCost
    gain_loss = round(proceeds - cost - book_value, 2)
    disposal = AssetDisposal(
        AssetID=asset_id,
        DisposalDate=data.DisposalDate,
        DisposalType=data.DisposalType,
        DisposalProceeds=proceeds,
        DisposalCost=cost,
        GainLossAmount=gain_loss,
        BookValueAtDisposal=book_value,
        Reference=data.Reference,
        Notes=data.Notes,
    )
    asset.Status = "Disposed"
    db.add(disposal)
    db.commit()
    db.refresh(disposal)
    return disposal
