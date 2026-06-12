from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.crm import Lead, Opportunity, Contact, Activity, Deal
from app.schemas.crm import (
    LeadCreate, LeadUpdate,
    OpportunityCreate, OpportunityUpdate,
    ContactCreate, ContactUpdate,
    ActivityCreate, ActivityUpdate,
    DealCreate, DealUpdate,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- Leads ---

def get_leads(
    db: Session,
    status: str | None = None,
    source: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Lead], int]:
    stmt = select(Lead)
    count_stmt = select(func.count(Lead.LeadID))
    if status:
        stmt = stmt.where(Lead.Status == status)
        count_stmt = count_stmt.where(Lead.Status == status)
    if source:
        stmt = stmt.where(Lead.Source == source)
        count_stmt = count_stmt.where(Lead.Source == source)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(Lead.CreatedAt.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def get_lead(db: Session, lead_id: int) -> Lead | None:
    return db.get(Lead, lead_id)


def create_lead(db: Session, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def update_lead(db: Session, lead_id: int, data: LeadUpdate) -> Lead | None:
    lead = db.get(Lead, lead_id)
    if not lead:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, val)
    lead.UpdatedAt = _utcnow()
    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, lead_id: int) -> bool:
    lead = db.get(Lead, lead_id)
    if not lead:
        return False
    db.delete(lead)
    db.commit()
    return True


def convert_lead_to_opportunity(db: Session, lead_id: int) -> Opportunity | None:
    lead = db.get(Lead, lead_id)
    if not lead or lead.ConvertedToOpportunity:
        return None
    opp = Opportunity(
        LeadID=lead.LeadID,
        OpportunityName=f"Opportunity from {lead.CompanyName}",
        Stage="Prospecting",
        AssignedTo=lead.AssignedTo,
    )
    db.add(opp)
    lead.ConvertedToOpportunity = True
    lead.UpdatedAt = _utcnow()
    db.commit()
    db.refresh(opp)
    return opp


# --- Opportunities ---

def get_opportunities(
    db: Session,
    stage: str | None = None,
    lead_id: int | None = None,
) -> list[Opportunity]:
    stmt = select(Opportunity)
    if stage:
        stmt = stmt.where(Opportunity.Stage == stage)
    if lead_id:
        stmt = stmt.where(Opportunity.LeadID == lead_id)
    stmt = stmt.order_by(Opportunity.CreatedAt.desc())
    return list(db.execute(stmt).scalars().all())


def get_opportunity(db: Session, opp_id: int) -> Opportunity | None:
    return db.get(Opportunity, opp_id)


def create_opportunity(db: Session, data: OpportunityCreate) -> Opportunity:
    opp = Opportunity(**data.model_dump())
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


def update_opportunity(db: Session, opp_id: int, data: OpportunityUpdate) -> Opportunity | None:
    opp = db.get(Opportunity, opp_id)
    if not opp:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(opp, key, val)
    if data.Stage == "Closed Won" and not opp.WonAt:
        opp.WonAt = _utcnow()
    opp.UpdatedAt = _utcnow()
    db.commit()
    db.refresh(opp)
    return opp


def delete_opportunity(db: Session, opp_id: int) -> bool:
    opp = db.get(Opportunity, opp_id)
    if not opp:
        return False
    db.delete(opp)
    db.commit()
    return True


# --- Contacts ---

def get_contacts(db: Session, client_code: str | None = None) -> list[Contact]:
    stmt = select(Contact)
    if client_code:
        stmt = stmt.where(Contact.ClientCode == client_code)
    stmt = stmt.order_by(Contact.LastName, Contact.FirstName)
    return list(db.execute(stmt).scalars().all())


def get_contact(db: Session, contact_id: int) -> Contact | None:
    return db.get(Contact, contact_id)


def create_contact(db: Session, data: ContactCreate) -> Contact:
    contact = Contact(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db: Session, contact_id: int, data: ContactUpdate) -> Contact | None:
    contact = db.get(Contact, contact_id)
    if not contact:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(contact, key, val)
    contact.UpdatedAt = _utcnow()
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact_id: int) -> bool:
    contact = db.get(Contact, contact_id)
    if not contact:
        return False
    db.delete(contact)
    db.commit()
    return True


# --- Activities ---

def get_activities(
    db: Session,
    opportunity_id: int | None = None,
    status: str | None = None,
) -> list[Activity]:
    stmt = select(Activity)
    if opportunity_id:
        stmt = stmt.where(Activity.OpportunityID == opportunity_id)
    if status:
        stmt = stmt.where(Activity.Status == status)
    stmt = stmt.order_by(Activity.ActivityDate.desc().nullslast(), Activity.CreatedAt.desc())
    return list(db.execute(stmt).scalars().all())


def get_activity(db: Session, activity_id: int) -> Activity | None:
    return db.get(Activity, activity_id)


def create_activity(db: Session, data: ActivityCreate) -> Activity:
    activity = Activity(**data.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def update_activity(db: Session, activity_id: int, data: ActivityUpdate) -> Activity | None:
    activity = db.get(Activity, activity_id)
    if not activity:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(activity, key, val)
    activity.UpdatedAt = _utcnow()
    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity_id: int) -> bool:
    activity = db.get(Activity, activity_id)
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True


# --- Deals ---

def get_deals(
    db: Session,
    stage: str | None = None,
    status: str | None = None,
) -> list[Deal]:
    stmt = select(Deal)
    if stage:
        stmt = stmt.where(Deal.Stage == stage)
    if status:
        stmt = stmt.where(Deal.Status == status)
    stmt = stmt.order_by(Deal.CreatedAt.desc())
    return list(db.execute(stmt).scalars().all())


def get_deal(db: Session, deal_id: int) -> Deal | None:
    return db.get(Deal, deal_id)


def create_deal(db: Session, data: DealCreate) -> Deal:
    deal = Deal(**data.model_dump())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def update_deal(db: Session, deal_id: int, data: DealUpdate) -> Deal | None:
    deal = db.get(Deal, deal_id)
    if not deal:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(deal, key, val)
    deal.UpdatedAt = _utcnow()
    db.commit()
    db.refresh(deal)
    return deal


def delete_deal(db: Session, deal_id: int) -> bool:
    deal = db.get(Deal, deal_id)
    if not deal:
        return False
    db.delete(deal)
    db.commit()
    return True
