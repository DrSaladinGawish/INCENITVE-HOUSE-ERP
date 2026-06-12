import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, Base
from app.models.prescription import Prescription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prescriptions", tags=["prescriptions"])


class PrescriptionInbound(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_id: str
    patient_name: str
    patient_id: str
    medication: str
    dosage: str
    prescribing_doctor: str
    notes: Optional[str] = None
    issued_at: Optional[str] = None

    @field_validator("external_id", "patient_name", "patient_id", "medication", "dosage", "prescribing_doctor")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class PrescriptionBatchInbound(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prescriptions: list[PrescriptionInbound]
    source: str = "bio-erp"


class PrescriptionOutbound(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)

    id: uuid.UUID
    external_id: str
    patient_name: str
    patient_id: str
    medication: str
    dosage: str
    prescribing_doctor: str
    notes: Optional[str] = None
    issued_at: Optional[str] = None
    received_at: str
    status: str


@router.post("/push", status_code=status.HTTP_201_CREATED, response_model=list[PrescriptionOutbound])
async def push_prescriptions(batch: PrescriptionBatchInbound, db: AsyncSession = Depends(get_db)):
    saved = []
    for item in batch.prescriptions:
        record = Prescription(
            external_id=item.external_id,
            patient_name=item.patient_name,
            patient_id=item.patient_id,
            medication=item.medication,
            dosage=item.dosage,
            prescribing_doctor=item.prescribing_doctor,
            notes=item.notes,
            issued_at=item.issued_at or datetime.now(timezone.utc).isoformat(),
            received_at=datetime.now(timezone.utc).isoformat(),
            status="pending",
        )
        db.add(record)
        saved.append(record)

    await db.flush()
    for rec in saved:
        logger.info("Received prescription external_id=%s -> local id=%s", rec.external_id, rec.id)

    return [_db_to_outbound(r) for r in saved]


@router.get("/", response_model=list[PrescriptionOutbound])
async def list_prescriptions(
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(Prescription).order_by(Prescription.created_at.desc())
    if status_filter:
        query = query.where(Prescription.status == status_filter)
    query = query.limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    return [_db_to_outbound(r) for r in records]


@router.get("/{external_id}", response_model=PrescriptionOutbound)
async def get_by_external_id(external_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prescription).where(Prescription.external_id == external_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return _db_to_outbound(record)


def _db_to_outbound(record: Prescription) -> PrescriptionOutbound:
    return PrescriptionOutbound(
        id=record.id,
        external_id=record.external_id,
        patient_name=record.patient_name,
        patient_id=record.patient_id,
        medication=record.medication,
        dosage=record.dosage,
        prescribing_doctor=record.prescribing_doctor,
        notes=record.notes,
        issued_at=record.issued_at,
        received_at=record.received_at,
        status=record.status,
    )
