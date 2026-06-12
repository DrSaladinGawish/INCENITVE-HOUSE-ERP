from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import inventory_service
from app.schemas.inventory import (
    ItemCreate, ItemUpdate, ItemResponse,
    WarehouseCreate, WarehouseUpdate, WarehouseResponse,
    StockMovementCreate, StockMovementResponse,
    InventoryCountCreate, InventoryCountResponse,
)

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


# ── Items ──

@router.get("/items", response_model=list[ItemResponse])
def list_items(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return inventory_service.get_items(db, skip=skip, limit=limit)


@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    return inventory_service.create_item(db, data)


@router.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db)):
    item = inventory_service.update_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    if not inventory_service.delete_item(db, item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


# ── Warehouses ──

@router.get("/warehouses", response_model=list[WarehouseResponse])
def list_warehouses(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return inventory_service.get_warehouses(db, skip=skip, limit=limit)


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    wh = inventory_service.get_warehouse(db, warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return wh


@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db)):
    return inventory_service.create_warehouse(db, data)


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(warehouse_id: int, data: WarehouseUpdate, db: Session = Depends(get_db)):
    wh = inventory_service.update_warehouse(db, warehouse_id, data)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return wh


@router.delete("/warehouses/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    if not inventory_service.delete_warehouse(db, warehouse_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")


# ── Stock Movements ──

@router.get("/movements", response_model=list[StockMovementResponse])
def list_movements(
    item_id: int | None = Query(None),
    warehouse_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items, _ = inventory_service.get_stock_movements(db, item_id=item_id, warehouse_id=warehouse_id, skip=skip, limit=limit)
    return items


@router.get("/movements/{movement_id}", response_model=StockMovementResponse)
def get_movement(movement_id: int, db: Session = Depends(get_db)):
    mov = inventory_service.get_stock_movement(db, movement_id)
    if not mov:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock movement not found")
    return mov


@router.post("/movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(data: StockMovementCreate, db: Session = Depends(get_db)):
    return inventory_service.create_stock_movement(db, data)


@router.delete("/movements/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movement(movement_id: int, db: Session = Depends(get_db)):
    if not inventory_service.delete_stock_movement(db, movement_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock movement not found")


# ── Inventory Counts ──

@router.get("/counts", response_model=list[InventoryCountResponse])
def list_counts(
    item_id: int | None = Query(None),
    warehouse_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items, _ = inventory_service.get_inventory_counts(db, item_id=item_id, warehouse_id=warehouse_id, skip=skip, limit=limit)
    return items


@router.get("/counts/{count_id}", response_model=InventoryCountResponse)
def get_count(count_id: int, db: Session = Depends(get_db)):
    cnt = inventory_service.get_inventory_count(db, count_id)
    if not cnt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory count not found")
    return cnt


@router.post("/counts", response_model=InventoryCountResponse, status_code=status.HTTP_201_CREATED)
def create_count(data: InventoryCountCreate, db: Session = Depends(get_db)):
    return inventory_service.create_inventory_count(db, data)


@router.post("/counts/{count_id}/adjust", response_model=InventoryCountResponse)
def adjust_count(count_id: int, db: Session = Depends(get_db)):
    cnt = inventory_service.adjust_inventory_count(db, count_id)
    if not cnt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Count not found or already adjusted")
    return cnt


# ── Stock Quantity (helper) ──

@router.get("/stock/{item_id}")
def get_stock_quantity(
    item_id: int,
    warehouse_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    qty = inventory_service._calculate_stock_quantity(db, item_id, warehouse_id)
    return {"item_id": item_id, "warehouse_id": warehouse_id, "quantity": qty}
