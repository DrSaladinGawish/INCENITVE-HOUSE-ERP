from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any

from app.database import get_db
from app.services.document import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


class ModuleOut(BaseModel):
    ModuleCode: str
    ModuleName: str
    Folder: str | None = None
    Description: str | None = None

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    DocumentID: int
    FileName: str
    FilePath: str | None = None
    FileSize: int | None = None
    SHA256: str | None = None
    MimeType: str | None = None
    ModuleCode: str | None = None
    LinkedEntityType: str | None = None
    LinkedEntityID: str | None = None
    PNRNumber: str | None = None
    Year: int | None = None
    Description: str | None = None
    Tags: str | None = None
    Status: str | None = None
    IsVerified: bool = False
    Version: int = 1
    CreatedAt: Any = None

    class Config:
        from_attributes = True


class IngestResponse(BaseModel):
    ingested: bool
    document_id: int | None = None
    file_name: str | None = None
    sha256: str | None = None
    module_code: str | None = None
    error: str | None = None


class VerifyResponse(BaseModel):
    verified: bool
    sha256: str | None = None
    match: bool | None = None
    file_size: int | None = None
    error: str | None = None


class LinkRequest(BaseModel):
    entity_type: str
    entity_id: str
    pnr_number: str | None = None


def _get_svc(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


@router.post("/seed-modules")
def seed_modules(svc: DocumentService = Depends(_get_svc)):
    modules = svc.seed_modules()
    return {"seeded": len(modules), "modules": [m.ModuleCode for m in modules]}


@router.get("/modules", response_model=list[ModuleOut])
def list_modules(svc: DocumentService = Depends(_get_svc)):
    return svc.list_modules()


@router.post("/ingest", response_model=IngestResponse)
def ingest_file(path: str = Query(..., description="Full path to file"), module_code: str | None = Query(None), svc: DocumentService = Depends(_get_svc)):
    return svc.ingest_file(path, module_code)


@router.post("/ingest-pnr2022")
def ingest_pnr2022(archive_path: str | None = Query(None), svc: DocumentService = Depends(_get_svc)):
    return svc.ingest_pnr2022(archive_path)


@router.get("", response_model=dict)
def search_documents(
    query: str | None = Query(None),
    module: str | None = Query(None),
    status: str | None = Query(None),
    pnr: str | None = Query(None),
    year: int | None = Query(None),
    entity_type: str | None = Query(None),
    verified: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    svc: DocumentService = Depends(_get_svc),
):
    skip = (page - 1) * page_size
    items, total = svc.search_documents(
        query=query, module_code=module, status=status,
        pnr_number=pnr, year=year, linked_entity_type=entity_type,
        verified=verified, skip=skip, limit=page_size,
    )
    return {"items": [DocumentOut.model_validate(d) for d in items], "total": total, "page": page, "page_size": page_size}


@router.get("/stats")
def get_stats(svc: DocumentService = Depends(_get_svc)):
    return svc.get_stats()


@router.get("/orphans")
def get_orphans(svc: DocumentService = Depends(_get_svc)):
    orphans = svc.get_orphans()
    return {"total": len(orphans), "items": [DocumentOut.model_validate(d) for d in orphans]}


@router.post("/auto-link")
def auto_link(svc: DocumentService = Depends(_get_svc)):
    return svc.auto_link()


@router.post("/verify-all")
def verify_all(svc: DocumentService = Depends(_get_svc)):
    return svc.verify_all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, svc: DocumentService = Depends(_get_svc)):
    doc = svc.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("/{doc_id}/verify", response_model=VerifyResponse)
def verify_document(doc_id: int, svc: DocumentService = Depends(_get_svc)):
    return svc.verify_document(doc_id)


@router.post("/{doc_id}/link")
def link_document(doc_id: int, req: LinkRequest, svc: DocumentService = Depends(_get_svc)):
    return svc.link_document(doc_id, req.entity_type, req.entity_id, req.pnr_number)
