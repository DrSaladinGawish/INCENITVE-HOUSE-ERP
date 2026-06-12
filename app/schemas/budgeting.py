from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class BudgetPeriodBase(BaseModel):
    BudgetPeriodCode: str = Field(..., max_length=10)
    FiscalYear: int
    Quarter: Optional[int] = None
    Month: Optional[int] = None
    Label: str = Field(..., max_length=100)
    StartDate: date
    EndDate: date


class BudgetPeriodCreate(BudgetPeriodBase):
    pass


class BudgetPeriodUpdate(BaseModel):
    Label: Optional[str] = Field(None, max_length=100)
    EndDate: Optional[date] = None
    IsClosed: Optional[bool] = None


class BudgetPeriodResponse(BudgetPeriodBase):
    IsClosed: bool
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class BudgetLineBase(BaseModel):
    BudgetPeriodCode: str = Field(..., max_length=10)
    AccountCode: Optional[str] = Field(None, max_length=20)
    Category: str = Field(..., max_length=50)
    Description: Optional[str] = None
    BudgetedAmount: float = 0
    Notes: Optional[str] = None


class BudgetLineCreate(BudgetLineBase):
    pass


class BudgetLineUpdate(BaseModel):
    AccountCode: Optional[str] = Field(None, max_length=20)
    Category: Optional[str] = Field(None, max_length=50)
    Description: Optional[str] = None
    BudgetedAmount: Optional[float] = None
    Notes: Optional[str] = None


class BudgetLineResponse(BudgetLineBase):
    BudgetLineID: int
    ActualAmount: float
    CommittedAmount: float
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class BudgetLineList(BaseModel):
    items: list[BudgetLineResponse]
    total: int
    page: int = 1
    page_size: int = 50


class BudgetCommitmentBase(BaseModel):
    BudgetLineID: int
    SourceType: Optional[str] = Field(None, max_length=50)
    SourceID: Optional[str] = Field(None, max_length=50)
    Amount: float


class BudgetCommitmentCreate(BudgetCommitmentBase):
    pass


class BudgetCommitmentResponse(BudgetCommitmentBase):
    CommitmentID: int
    CreatedAt: datetime

    class Config:
        from_attributes = True


class BudgetRevisionBase(BaseModel):
    BudgetLineID: int
    PreviousAmount: float
    NewAmount: float
    Reason: Optional[str] = None
    RevisedBy: Optional[str] = Field(None, max_length=50)


class BudgetRevisionCreate(BudgetRevisionBase):
    pass


class BudgetRevisionResponse(BudgetRevisionBase):
    RevisionID: int
    RevisedAt: datetime

    class Config:
        from_attributes = True


class BudgetVsActualItem(BaseModel):
    BudgetLineID: int
    BudgetPeriodCode: str
    Category: str
    Description: Optional[str] = None
    BudgetedAmount: float
    ActualAmount: float
    CommittedAmount: float
    RemainingBudget: float
    UtilizationPct: float


class BudgetVsActualResponse(BaseModel):
    period: Optional[BudgetPeriodResponse] = None
    items: list[BudgetVsActualItem]
    total_budgeted: float
    total_actual: float
    total_committed: float
    total_variance: float
