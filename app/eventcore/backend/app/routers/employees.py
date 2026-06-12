from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.employee import Employee, LeaveRequest, TaskAssignment
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    LeaveRequestCreate, LeaveRequestResponse,
    TaskAssignmentCreate, TaskAssignmentResponse,
)

router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(payload: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    emp = Employee(**payload.model_dump())
    db.add(emp)
    await db.flush()
    await db.refresh(emp)
    return emp


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    department: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Employee).order_by(Employee.full_name)
    if department:
        q = q.where(Employee.department == department)
    if status:
        q = q.where(Employee.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    return emp


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: UUID, payload: EmployeeUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(emp, key, val)
    await db.flush()
    await db.refresh(emp)
    return emp


@router.get("/dashboard/stats")
async def get_employee_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(Employee.id))) or 0
    active = await db.scalar(select(func.count(Employee.id)).where(Employee.status == "active")) or 0
    depts = await db.execute(select(Employee.department, func.count(Employee.id)).where(Employee.status == "active").group_by(Employee.department))
    return {
        "total_employees": total,
        "active_employees": active,
        "departments": [{"department": d, "count": c} for d, c in depts.all()],
    }


# Leave Requests
@router.post("/leave", response_model=LeaveRequestResponse, status_code=201)
async def create_leave_request(payload: LeaveRequestCreate, db: AsyncSession = Depends(get_db)):
    lr = LeaveRequest(**payload.model_dump())
    db.add(lr)
    await db.flush()
    await db.refresh(lr)
    return lr


@router.get("/leave", response_model=list[LeaveRequestResponse])
async def list_leave_requests(
    employee_id: UUID | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(LeaveRequest).order_by(LeaveRequest.created_at.desc())
    if employee_id:
        q = q.where(LeaveRequest.employee_id == employee_id)
    if status:
        q = q.where(LeaveRequest.status == status)
    result = await db.execute(q)
    return result.scalars().all()


# Task Assignments
@router.post("/tasks", response_model=TaskAssignmentResponse, status_code=201)
async def create_task(payload: TaskAssignmentCreate, db: AsyncSession = Depends(get_db)):
    task = TaskAssignment(**payload.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskAssignmentResponse])
async def list_tasks(
    job_id: UUID | None = Query(None),
    employee_id: UUID | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(TaskAssignment).order_by(TaskAssignment.created_at.desc())
    if job_id:
        q = q.where(TaskAssignment.job_id == job_id)
    if employee_id:
        q = q.where(TaskAssignment.employee_id == employee_id)
    if status:
        q = q.where(TaskAssignment.status == status)
    result = await db.execute(q)
    return result.scalars().all()
