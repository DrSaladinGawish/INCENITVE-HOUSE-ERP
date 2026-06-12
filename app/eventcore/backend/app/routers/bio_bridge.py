"""BIO Bridge router — endpoints for syncing with BIO_ERP."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.bio_bridge import (
    sync_vendors_from_bio,
    sync_gl_accounts_from_bio,
    post_invoice_to_bio,
)

router = APIRouter(prefix="/api/v1/bridge", tags=["BIO Bridge"])


@router.post("/sync/vendors")
async def sync_vendors(db: AsyncSession = Depends(get_db)):
    result = await sync_vendors_from_bio(db)
    return result


@router.post("/sync/gl-accounts")
async def sync_gl_accounts(db: AsyncSession = Depends(get_db)):
    result = await sync_gl_accounts_from_bio(db)
    return result


@router.post("/invoice/{invoice_id}/post-to-bio")
async def post_invoice_to_bio_endpoint(invoice_id: str):
    from app.services.bio_bridge import post_invoice_to_bio
    result = await post_invoice_to_bio({"id": invoice_id})
    return result


@router.get("/status")
async def bridge_status():
    from app.config import settings
    return {
        "bio_erp_configured": bool(settings.bio_erp_base_url and settings.bio_erp_api_key),
        "bio_erp_base_url": settings.bio_erp_base_url,
        "vendor_sync_interval": settings.bio_erp_vendor_sync_interval,
        "gl_sync_enabled": settings.bio_erp_gl_sync_enabled,
        "po_approval_workflow": settings.bio_erp_po_approval_workflow,
    }
