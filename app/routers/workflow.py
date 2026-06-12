from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import workflow_service as wfs

router = APIRouter(prefix="/workflow", tags=["Workflow"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def workflow_dashboard(request: Request, db: Session = Depends(get_db)):
    workflows = wfs.get_workflows(db)
    requests, total = wfs.get_approval_requests(db)
    return templates.TemplateResponse("workflow/dashboard.html", {
        "request": request, "workflows": workflows, "requests": requests, "total": total,
    })


@router.get("/approvals", response_class=HTMLResponse)
def approval_list(
    request: Request,
    status: str | None = Query(None),
    module: str | None = Query(None),
    db: Session = Depends(get_db),
):
    requests, total = wfs.get_approval_requests(db, status=status, module=module)
    return templates.TemplateResponse("workflow/approval_list.html", {
        "request": request, "requests": requests, "total": total,
    })


@router.get("/approvals/{approval_id}", response_class=HTMLResponse)
def approval_detail(request: Request, approval_id: int, db: Session = Depends(get_db)):
    req = wfs.get_approval_request(db, approval_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    history = wfs.get_approval_history(db, approval_id)
    return templates.TemplateResponse("workflow/approval_detail.html", {
        "request": request, "req": req, "history": history,
    })


@router.post("/api/approvals/create")
def api_create_approval(
    workflow_id: int = Query(...),
    module: str = Query(...),
    reference_id: str = Query(...),
    requested_by: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        req = wfs.create_approval_request(db, workflow_id, module, reference_id, requested_by)
        return {"detail": "Approval request created", "approval_id": req.ApprovalID}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/approvals/{approval_id}/approve")
def api_approve(
    approval_id: int,
    approved_by: str = Query(...),
    comments: str = Query(""),
    db: Session = Depends(get_db),
):
    req = wfs.approve_request(db, approval_id, approved_by, comments)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {"detail": "Approved", "status": req.Status}


@router.post("/api/approvals/{approval_id}/reject")
def api_reject(
    approval_id: int,
    rejected_by: str = Query(...),
    comments: str = Query(""),
    db: Session = Depends(get_db),
):
    req = wfs.reject_request(db, approval_id, rejected_by, comments)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {"detail": "Rejected", "status": req.Status}


@router.post("/api/workflows/create")
def api_create_workflow(
    name: str = Query(...),
    module: str = Query(...),
    description: str = Query(""),
    db: Session = Depends(get_db),
):
    wf = wfs.create_workflow(db, name, module, description)
    return {"detail": "Workflow created", "workflow_id": wf.WorkflowID}


@router.post("/api/workflows/{workflow_id}/states")
def api_add_state(
    workflow_id: int,
    state_name: str = Query(...),
    state_order: int = Query(0),
    required_role: str = Query(""),
    db: Session = Depends(get_db),
):
    ws = wfs.add_workflow_state(db, workflow_id, state_name, state_order, required_role)
    return {"detail": "State added", "state_id": ws.StateID}
