from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import crm_service
from app.schemas.crm import (
    LeadCreate, LeadUpdate, LeadResponse, LeadList,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    ContactCreate, ContactUpdate, ContactResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    DealCreate, DealUpdate, DealResponse,
)

router = APIRouter(prefix="/api/crm", tags=["CRM"])


@router.get("/leads", response_model=LeadList)
def list_leads(
    status: str | None = Query(None),
    source: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = crm_service.get_leads(db, status=status, source=source, skip=skip, limit=page_size)
    return LeadList(items=items, total=total, page=page, page_size=page_size)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = crm_service.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    return crm_service.create_lead(db, data)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    lead = crm_service.update_lead(db, lead_id, data)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    if not crm_service.delete_lead(db, lead_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")


@router.post("/leads/{lead_id}/convert", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def convert_lead(lead_id: int, db: Session = Depends(get_db)):
    opp = crm_service.convert_lead_to_opportunity(db, lead_id)
    if not opp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lead not found or already converted")
    return opp


@router.get("/opportunities", response_model=list[OpportunityResponse])
def list_opportunities(
    stage: str | None = Query(None),
    lead_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return crm_service.get_opportunities(db, stage=stage, lead_id=lead_id)


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
def get_opportunity(opp_id: int, db: Session = Depends(get_db)):
    opp = crm_service.get_opportunity(db, opp_id)
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opp


@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(data: OpportunityCreate, db: Session = Depends(get_db)):
    return crm_service.create_opportunity(db, data)


@router.put("/opportunities/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(opp_id: int, data: OpportunityUpdate, db: Session = Depends(get_db)):
    opp = crm_service.update_opportunity(db, opp_id, data)
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opp


@router.delete("/opportunities/{opp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(opp_id: int, db: Session = Depends(get_db)):
    if not crm_service.delete_opportunity(db, opp_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")


@router.get("/contacts", response_model=list[ContactResponse])
def list_contacts(client_code: str | None = Query(None), db: Session = Depends(get_db)):
    return crm_service.get_contacts(db, client_code=client_code)


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = crm_service.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(data: ContactCreate, db: Session = Depends(get_db)):
    return crm_service.create_contact(db, data)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db)):
    contact = crm_service.update_contact(db, contact_id, data)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    if not crm_service.delete_contact(db, contact_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")


@router.get("/activities", response_model=list[ActivityResponse])
def list_activities(
    opportunity_id: int | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return crm_service.get_activities(db, opportunity_id=opportunity_id, status=status)


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = crm_service.get_activity(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(data: ActivityCreate, db: Session = Depends(get_db)):
    return crm_service.create_activity(db, data)


@router.put("/activities/{activity_id}", response_model=ActivityResponse)
def update_activity(activity_id: int, data: ActivityUpdate, db: Session = Depends(get_db)):
    activity = crm_service.update_activity(db, activity_id, data)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    if not crm_service.delete_activity(db, activity_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")


@router.get("/deals", response_model=list[DealResponse])
def list_deals(
    stage: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return crm_service.get_deals(db, stage=stage, status=status)


@router.get("/deals/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = crm_service.get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal


@router.post("/deals", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
def create_deal(data: DealCreate, db: Session = Depends(get_db)):
    return crm_service.create_deal(db, data)


@router.put("/deals/{deal_id}", response_model=DealResponse)
def update_deal(deal_id: int, data: DealUpdate, db: Session = Depends(get_db)):
    deal = crm_service.update_deal(db, deal_id, data)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal


@router.delete("/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    if not crm_service.delete_deal(db, deal_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
