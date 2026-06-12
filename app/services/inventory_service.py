from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.inventory import Item, Warehouse, StockMovement, InventoryCount
from app.schemas.inventory import (
    ItemCreate, ItemUpdate,
    WarehouseCreate, WarehouseUpdate,
    StockMovementCreate,
    InventoryCountCreate,
)


def _calculate_stock_quantity(db: Session, item_id: int, warehouse_id: int | None = None) -> float:
    stmt = select(func.coalesce(func.sum(StockMovement.Quantity), 0)).where(
        StockMovement.ItemID == item_id,
    )
    if warehouse_id:
        stmt = stmt.where(StockMovement.WarehouseID == warehouse_id)
    result = db.execute(stmt).scalar() or 0
    return float(result)


# --- Items ---

def get_items(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
    stmt = select(Item).order_by(Item.ItemName).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_item(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def get_item_by_code(db: Session, item_code: str) -> Item | None:
    stmt = select(Item).where(Item.ItemCode == item_code)
    return db.execute(stmt).scalar_one_or_none()


def create_item(db: Session, data: ItemCreate) -> Item:
    item = Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_id: int, data: ItemUpdate) -> Item | None:
    item = db.get(Item, item_id)
    if not item:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> bool:
    item = db.get(Item, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


# --- Warehouses ---

def get_warehouses(db: Session, skip: int = 0, limit: int = 100) -> list[Warehouse]:
    stmt = select(Warehouse).order_by(Warehouse.WarehouseName).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_warehouse(db: Session, warehouse_id: int) -> Warehouse | None:
    return db.get(Warehouse, warehouse_id)


def create_warehouse(db: Session, data: WarehouseCreate) -> Warehouse:
    wh = Warehouse(**data.model_dump())
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


def update_warehouse(db: Session, warehouse_id: int, data: WarehouseUpdate) -> Warehouse | None:
    wh = db.get(Warehouse, warehouse_id)
    if not wh:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(wh, key, val)
    db.commit()
    db.refresh(wh)
    return wh


def delete_warehouse(db: Session, warehouse_id: int) -> bool:
    wh = db.get(Warehouse, warehouse_id)
    if not wh:
        return False
    db.delete(wh)
    db.commit()
    return True


# --- Stock Movements ---

def get_stock_movements(
    db: Session,
    item_id: int | None = None,
    warehouse_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[StockMovement], int]:
    stmt = select(StockMovement)
    count_stmt = select(func.count(StockMovement.MovementID))
    if item_id:
        stmt = stmt.where(StockMovement.ItemID == item_id)
        count_stmt = count_stmt.where(StockMovement.ItemID == item_id)
    if warehouse_id:
        stmt = stmt.where(StockMovement.WarehouseID == warehouse_id)
        count_stmt = count_stmt.where(StockMovement.WarehouseID == warehouse_id)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(StockMovement.MovementDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def get_stock_movement(db: Session, movement_id: int) -> StockMovement | None:
    return db.get(StockMovement, movement_id)


def create_stock_movement(db: Session, data: StockMovementCreate) -> StockMovement:
    total_value = (data.UnitPrice or 0) * data.Quantity
    mov = StockMovement(
        ItemID=data.ItemID,
        WarehouseID=data.WarehouseID,
        MovementType=data.MovementType,
        Quantity=data.Quantity,
        UnitPrice=data.UnitPrice,
        TotalValue=total_value,
        Reference=data.Reference,
        ReferenceType=data.ReferenceType,
        Narration=data.Narration,
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov


def delete_stock_movement(db: Session, movement_id: int) -> bool:
    mov = db.get(StockMovement, movement_id)
    if not mov:
        return False
    db.delete(mov)
    db.commit()
    return True


# --- Inventory Counts ---

def get_inventory_counts(
    db: Session,
    item_id: int | None = None,
    warehouse_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[InventoryCount], int]:
    stmt = select(InventoryCount)
    count_stmt = select(func.count(InventoryCount.CountID))
    if item_id:
        stmt = stmt.where(InventoryCount.ItemID == item_id)
        count_stmt = count_stmt.where(InventoryCount.ItemID == item_id)
    if warehouse_id:
        stmt = stmt.where(InventoryCount.WarehouseID == warehouse_id)
        count_stmt = count_stmt.where(InventoryCount.WarehouseID == warehouse_id)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(InventoryCount.CountDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def get_inventory_count(db: Session, count_id: int) -> InventoryCount | None:
    return db.get(InventoryCount, count_id)


def create_inventory_count(db: Session, data: InventoryCountCreate) -> InventoryCount:
    expected = _calculate_stock_quantity(db, data.ItemID, data.WarehouseID)
    variance = data.ActualQuantity - expected
    cnt = InventoryCount(
        ItemID=data.ItemID,
        WarehouseID=data.WarehouseID,
        ExpectedQuantity=expected,
        ActualQuantity=data.ActualQuantity,
        Variance=variance,
        CountedBy=data.CountedBy,
        Remarks=data.Remarks,
    )
    db.add(cnt)
    db.commit()
    db.refresh(cnt)
    return cnt


def adjust_inventory_count(db: Session, count_id: int) -> InventoryCount | None:
    cnt = db.get(InventoryCount, count_id)
    if not cnt or cnt.IsAdjusted:
        return None
    variance = cnt.ActualQuantity - (cnt.ExpectedQuantity or 0)
    mov = StockMovement(
        ItemID=cnt.ItemID,
        WarehouseID=cnt.WarehouseID,
        MovementType="Adjustment",
        Quantity=variance,
        UnitPrice=0,
        TotalValue=0,
        Reference=f"Count#{cnt.CountID}",
        ReferenceType="InventoryCount",
        Narration=f"Auto-adjustment from inventory count #{cnt.CountID}",
    )
    db.add(mov)
    cnt.IsAdjusted = True
    db.commit()
    db.refresh(cnt)
    return cnt
