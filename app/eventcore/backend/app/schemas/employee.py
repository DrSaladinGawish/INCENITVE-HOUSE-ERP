from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    salary: float = 0
    currency: str = "EGP"


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    salary: float
    currency: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LeaveRequestCreate(BaseModel):
    employee_id: UUID
    leave_type: str = "annual"
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskAssignmentCreate(BaseModel):
    job_id: UUID
    employee_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str = "medium"


class TaskAssignmentResponse(BaseModel):
    id: UUID
    job_id: UUID
    employee_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
