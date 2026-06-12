from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.workflow_models import (
    WorkflowDefinition,
    WorkflowState,
    ApprovalRequest,
    ApprovalHistory,
)


def get_workflows(db: Session) -> list[WorkflowDefinition]:
    stmt = select(WorkflowDefinition).order_by(WorkflowDefinition.WorkflowName)
    return list(db.execute(stmt).scalars().all())


def get_workflow(db: Session, workflow_id: int) -> WorkflowDefinition | None:
    return db.get(WorkflowDefinition, workflow_id)


def create_workflow(db: Session, name: str, module: str, description: str = "") -> WorkflowDefinition:
    wf = WorkflowDefinition(WorkflowName=name, Module=module, Description=description)
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf


def add_workflow_state(db: Session, workflow_id: int, state_name: str, order: int = 0, role: str = "") -> WorkflowState:
    ws = WorkflowState(WorkflowID=workflow_id, StateName=state_name, StateOrder=order, RequiredRole=role or None)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def get_approval_requests(
    db: Session,
    status: str | None = None,
    module: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ApprovalRequest], int]:
    stmt = select(ApprovalRequest)
    if status:
        stmt = stmt.where(ApprovalRequest.Status == status)
    if module:
        stmt = stmt.where(ApprovalRequest.ReferenceModule == module)
    total = len(db.execute(stmt).scalars().all())
    stmt = stmt.order_by(ApprovalRequest.RequestedAt.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def get_approval_request(db: Session, approval_id: int) -> ApprovalRequest | None:
    return db.get(ApprovalRequest, approval_id)


def create_approval_request(
    db: Session,
    workflow_id: int,
    module: str,
    reference_id: str,
    requested_by: str,
) -> ApprovalRequest:
    wf = db.get(WorkflowDefinition, workflow_id)
    if not wf or not wf.states:
        raise ValueError("Workflow not found or has no states")
    first_state = min(wf.states, key=lambda s: s.StateOrder)
    req = ApprovalRequest(
        WorkflowID=workflow_id,
        StateID=first_state.StateID,
        ReferenceModule=module,
        ReferenceID=reference_id,
        RequestedBy=requested_by,
        Status="Pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def approve_request(db: Session, approval_id: int, approved_by: str, comments: str = "") -> ApprovalRequest | None:
    req = db.get(ApprovalRequest, approval_id)
    if not req:
        return None
    req.Status = "Approved"
    req.ApprovedBy = approved_by
    req.ApprovedAt = datetime.utcnow()
    req.Comments = comments
    db.flush()

    history = ApprovalHistory(ApprovalID=approval_id, Action="Approved", ActionBy=approved_by, Comments=comments)
    db.add(history)
    db.commit()
    db.refresh(req)
    return req


def reject_request(db: Session, approval_id: int, rejected_by: str, comments: str = "") -> ApprovalRequest | None:
    req = db.get(ApprovalRequest, approval_id)
    if not req:
        return None
    req.Status = "Rejected"
    req.ApprovedBy = rejected_by
    req.ApprovedAt = datetime.utcnow()
    req.Comments = comments
    db.flush()

    history = ApprovalHistory(ApprovalID=approval_id, Action="Rejected", ActionBy=rejected_by, Comments=comments)
    db.add(history)
    db.commit()
    db.refresh(req)
    return req


def get_approval_history(db: Session, approval_id: int) -> list[ApprovalHistory]:
    stmt = select(ApprovalHistory).where(
        ApprovalHistory.ApprovalID == approval_id
    ).order_by(ApprovalHistory.ActionAt)
    return list(db.execute(stmt).scalars().all())
