from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class VendorResponse(BaseModel):
    id: UUID
    name: str
    category: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vat_number: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}
