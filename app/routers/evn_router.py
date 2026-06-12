from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import evn_service
from app.schemas.evn import (
    PNRMasterCreate, PNRMasterUpdate, PNRMasterResponse,
    PNRBudgetLineItemCreate, PNRBudgetLineItemUpdate, PNRBudgetLineItemResponse,
    ServiceMainCategoryResponse, ServiceSubCategoryResponse, ServiceTypeResponse,
)

router = APIRouter(prefix="/api/evn", tags=["Events"])


@router.get("/pnrs", response_model=dict)
def list_pnrs(
    year: int | None = Query(None),
    status: str | None = Query(None),
    client_code: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = evn_service.get_pnrs(db, year=year, status=status, client_code=client_code, skip=skip, limit=page_size)
    return {"items": [PNRMasterResponse.model_validate(p) for p in items], "total": total, "page": page, "page_size": page_size}


@router.get("/pnrs/{pnr_number}", response_model=PNRMasterResponse)
def get_pnr(pnr_number: str, db: Session = Depends(get_db)):
    pnr = evn_service.get_pnr(db, pnr_number)
    if not pnr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PNR not found")
    return pnr


@router.post("/pnrs", response_model=PNRMasterResponse, status_code=status.HTTP_201_CREATED)
def create_pnr(data: PNRMasterCreate, db: Session = Depends(get_db)):
    return evn_service.create_pnr(db, data)


@router.put("/pnrs/{pnr_number}", response_model=PNRMasterResponse)
def update_pnr(pnr_number: str, data: PNRMasterUpdate, db: Session = Depends(get_db)):
    pnr = evn_service.update_pnr(db, pnr_number, data)
    if not pnr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PNR not found")
    return pnr


@router.delete("/pnrs/{pnr_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pnr(pnr_number: str, db: Session = Depends(get_db)):
    if not evn_service.delete_pnr(db, pnr_number):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PNR not found")


@router.get("/categories", response_model=list[ServiceMainCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return evn_service.get_service_categories(db)


@router.get("/sub-categories", response_model=list[ServiceSubCategoryResponse])
def list_sub_categories(main_code: str | None = Query(None), db: Session = Depends(get_db)):
    return evn_service.get_service_sub_categories(db, main_code=main_code)


@router.get("/service-types", response_model=list[ServiceTypeResponse])
def list_service_types(sub_code: str | None = Query(None), db: Session = Depends(get_db)):
    return evn_service.get_service_types(db, sub_code=sub_code)


@router.get("/budget-lines", response_model=dict)
def list_budget_lines(
    pnr_number: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = evn_service.get_budget_line_items(db, pnr_number=pnr_number, skip=skip, limit=page_size)
    return {"items": [PNRBudgetLineItemResponse.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}


@router.post("/budget-lines", response_model=PNRBudgetLineItemResponse, status_code=status.HTTP_201_CREATED)
def create_budget_line(data: PNRBudgetLineItemCreate, db: Session = Depends(get_db)):
    return evn_service.create_budget_line_item(db, data)


@router.put("/budget-lines/{line_item_id}", response_model=PNRBudgetLineItemResponse)
def update_budget_line(line_item_id: int, data: PNRBudgetLineItemUpdate, db: Session = Depends(get_db)):
    item = evn_service.update_budget_line_item(db, line_item_id, data)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget line item not found")
    return item


@router.delete("/budget-lines/{line_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_line(line_item_id: int, db: Session = Depends(get_db)):
    if not evn_service.delete_budget_line_item(db, line_item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget line item not found")


@router.get("/pnrs/{pnr_number}/budget-summary")
def pnr_budget_summary(pnr_number: str, db: Session = Depends(get_db)):
    return evn_service.get_pnr_budget_summary(db, pnr_number)
