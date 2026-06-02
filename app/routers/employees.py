import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import EmployeeDim, EmployeeAssignment, EventDim, AuditTrail
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeAssignmentCreate, EmployeeAssignmentResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["employees"])


@router.get("/", response_model=list[EmployeeResponse])
async def list_employees(
    department: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(EmployeeDim)
    if department:
        q = q.where(EmployeeDim.department == department)
    if status:
        q = q.where(EmployeeDim.status == status)
    if search:
        q = q.where(EmployeeDim.name.ilike(f"%{search}%") | EmployeeDim.employee_code.ilike(f"%{search}%"))
    q = q.offset(offset).limit(limit).order_by(EmployeeDim.name)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmployeeDim).where(EmployeeDim.employee_id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("/", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    existing = await db.execute(select(EmployeeDim).where(EmployeeDim.employee_code == data.employee_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Employee code already exists")
    emp = EmployeeDim(**data.model_dump())
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    audit = AuditTrail(table_name="employee_dim", record_id=emp.employee_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return emp


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(EmployeeDim).where(EmployeeDim.employee_id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    old_vals = {c.name: getattr(emp, c.name) for c in EmployeeDim.__table__.columns}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(emp, k, v)
    emp.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(emp)
    audit = AuditTrail(table_name="employee_dim", record_id=employee_id, action="UPDATE", old_values=json.loads(json.dumps(old_vals, default=str)), new_values=json.loads(json.dumps(data.model_dump(exclude_unset=True), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return emp


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(EmployeeDim).where(EmployeeDim.employee_id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.status = "inactive"
    emp.updated_at = datetime.datetime.utcnow()
    await db.commit()
    audit = AuditTrail(table_name="employee_dim", record_id=employee_id, action="DEACTIVATE", new_values={"status": "inactive"}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Employee deactivated"}


@router.post("/assignments", response_model=EmployeeAssignmentResponse, status_code=201)
async def create_assignment(
    data: EmployeeAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "event_manager")),
):
    emp = await db.execute(select(EmployeeDim).where(EmployeeDim.employee_id == data.employee_id))
    if not emp.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Employee not found")
    evt = await db.execute(select(EventDim).where(EventDim.event_id == data.event_id))
    if not evt.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")
    emp_obj = emp.scalar_one()
    cost = (data.hours_worked * emp_obj.hourly_rate) + (data.overtime_hours * emp_obj.overtime_rate)
    assign = EmployeeAssignment(**data.model_dump(), cost=cost)
    db.add(assign)
    await db.commit()
    await db.refresh(assign)
    return assign


@router.get("/assignments/event/{event_id}")
async def get_event_assignments(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmployeeAssignment).where(EmployeeAssignment.event_id == event_id).order_by(EmployeeAssignment.assignment_date)
    )
    return result.scalars().all()


@router.get("/{employee_id}/assignments")
async def get_employee_assignments(employee_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmployeeAssignment).where(EmployeeAssignment.employee_id == employee_id).order_by(EmployeeAssignment.assignment_date.desc())
    )
    return result.scalars().all()
