"""BIO Bridge — HTTP client for syncing with BIO_ERP system."""
import uuid
import httpx
from typing import Optional
from app.config import settings


async def sync_vendors_from_bio(db_session) -> dict:
    """Fetch vendors from BIO_ERP and upsert into EventCore."""
    if not settings.bio_erp_base_url or not settings.bio_erp_api_key:
        return {"status": "skipped", "reason": "BIO_ERP not configured"}

    from app.models.vendor import Vendor

    async with httpx.AsyncClient(base_url=settings.bio_erp_base_url, timeout=30) as client:
        try:
            resp = await client.get(
                "/api/vendors",
                headers={
                    "Authorization": f"Bearer {settings.bio_erp_api_key}",
                    "X-Correlation-ID": str(uuid.uuid4()),
                },
            )
            resp.raise_for_status()
            bio_vendors = resp.json()
        except httpx.HTTPError as e:
            return {"status": "error", "message": str(e)}

    imported = 0
    for v in bio_vendors:
        existing = await db_session.execute(
            select(Vendor).where(Vendor.bio_vendor_id == v.get("id"))
        )
        vendor = existing.scalar_one_or_none()
        if vendor:
            vendor.name = v.get("name", vendor.name)
            vendor.email = v.get("email")
            vendor.phone = v.get("phone")
            vendor.vat_number = v.get("vat_number")
            vendor.bank_account = v.get("bank_account")
        else:
            vendor = Vendor(
                bio_vendor_id=v.get("id"),
                name=v.get("name"),
                category=v.get("category"),
                email=v.get("email"),
                phone=v.get("phone"),
                vat_number=v.get("vat_number"),
                bank_account=v.get("bank_account"),
            )
            db_session.add(vendor)
        imported += 1

    await db_session.flush()
    return {"status": "success", "imported": imported}


async def sync_gl_accounts_from_bio(db_session) -> dict:
    """Fetch GL accounts from BIO_ERP for reference."""
    if not settings.bio_erp_base_url or not settings.bio_erp_api_key:
        return {"status": "skipped", "reason": "BIO_ERP not configured"}

    async with httpx.AsyncClient(base_url=settings.bio_erp_base_url, timeout=30) as client:
        try:
            resp = await client.get(
                "/api/gl-accounts",
                headers={
                    "Authorization": f"Bearer {settings.bio_erp_api_key}",
                    "X-Correlation-ID": str(uuid.uuid4()),
                },
            )
            resp.raise_for_status()
            return {"status": "success", "accounts": resp.json()}
        except httpx.HTTPError as e:
            return {"status": "error", "message": str(e)}


async def post_invoice_to_bio(invoice_data: dict) -> dict:
    """Post a sales invoice to BIO_ERP as a journal entry."""
    if not settings.bio_erp_base_url or not settings.bio_erp_api_key:
        return {"status": "skipped", "reason": "BIO_ERP not configured"}

    async with httpx.AsyncClient(base_url=settings.bio_erp_base_url, timeout=30) as client:
        try:
            resp = await client.post(
                "/api/journal-entries",
                json=invoice_data,
                headers={
                    "Authorization": f"Bearer {settings.bio_erp_api_key}",
                    "Content-Type": "application/json",
                    "X-Correlation-ID": str(uuid.uuid4()),
                    "Idempotency-Key": str(uuid.uuid4()),
                },
            )
            resp.raise_for_status()
            return {"status": "posted", "bio_entry_id": resp.json().get("id")}
        except httpx.HTTPError as e:
            return {"status": "error", "message": str(e)}
