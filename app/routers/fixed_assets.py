from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import fixed_assets_service
from app.schemas.fixed_assets import (
    AssetCategoryCreate, AssetCategoryUpdate, AssetCategoryResponse,
    AssetCreate, AssetUpdate, AssetResponse, AssetDetailResponse,
    DepreciationCreate, DepreciationResponse, DepreciationScheduleResponse,
    AssetDisposalCreate, AssetDisposalResponse, AssetList,
)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/api/fixed-assets", tags=["Fixed Assets"])
page_router = APIRouter(tags=["Fixed Assets Pages"])


@page_router.get("/fixed-assets", response_class=HTMLResponse)
def assets_list_page(request: Request):
    return templates.TemplateResponse("assets_list.html", {"request": request})


@page_router.get("/fixed-assets/new", response_class=HTMLResponse)
def asset_new_page(request: Request):
    return templates.TemplateResponse("asset_form.html", {
        "request": request, "title": "New Fixed Asset",
        "subtitle": "Register a new asset in the system", "asset": None,
    })


@page_router.get("/fixed-assets/{asset_id}", response_class=HTMLResponse)
def asset_detail_page(request: Request, asset_id: int, db: Session = Depends(get_db)):
    asset = fixed_assets_service.get_asset(db, asset_id)
    if not asset:
        return HTMLResponse(content="Asset not found", status_code=404)
    return templates.TemplateResponse("asset_form.html", {
        "request": request, "title": "Edit Asset - " + asset.AssetCode,
        "subtitle": "Update asset details and view depreciation", "asset": asset,
    })


@router.get("/categories", response_model=list[AssetCategoryResponse])
def list_categories(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return fixed_assets_service.get_categories(db, skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=AssetCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = fixed_assets_service.get_category(db, category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


@router.post("/categories", response_model=AssetCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: AssetCategoryCreate, db: Session = Depends(get_db)):
    return fixed_assets_service.create_category(db, data)


@router.put("/categories/{category_id}", response_model=AssetCategoryResponse)
def update_category(category_id: int, data: AssetCategoryUpdate, db: Session = Depends(get_db)):
    cat = fixed_assets_service.update_category(db, category_id, data)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    if not fixed_assets_service.delete_category(db, category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


@router.get("", response_model=AssetList)
def list_assets(
    category_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = fixed_assets_service.get_assets(db, category_id=category_id, status=status, skip=skip, limit=page_size)
    return AssetList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{asset_id}", response_model=AssetDetailResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = fixed_assets_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    return fixed_assets_service.create_asset(db, data)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    asset = fixed_assets_service.update_asset(db, asset_id, data)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    if not fixed_assets_service.delete_asset(db, asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")


@router.get("/{asset_id}/depreciation-schedule", response_model=DepreciationScheduleResponse)
def get_depreciation_schedule(asset_id: int, db: Session = Depends(get_db)):
    asset = fixed_assets_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return fixed_assets_service.compute_depreciation_schedule(asset)


@router.post("/{asset_id}/depreciation", response_model=DepreciationResponse, status_code=status.HTTP_201_CREATED)
def post_depreciation(asset_id: int, data: DepreciationCreate, db: Session = Depends(get_db)):
    return fixed_assets_service.post_depreciation(db, data)


@router.get("/{asset_id}/depreciation", response_model=list[DepreciationResponse])
def list_depreciation(asset_id: int, db: Session = Depends(get_db)):
    return fixed_assets_service.get_depreciation_entries(db, asset_id)


@router.post("/{asset_id}/dispose", response_model=AssetDisposalResponse, status_code=status.HTTP_201_CREATED)
def dispose_asset(asset_id: int, data: AssetDisposalCreate, db: Session = Depends(get_db)):
    return fixed_assets_service.dispose_asset(db, asset_id, data)
