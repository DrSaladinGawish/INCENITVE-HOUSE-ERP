from datetime import date, datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SalaryStructure(Base):
    __tablename__ = "SalaryStructure"
    __table_args__ = {"schema": "dbo"}
    SalaryStructureID = Column(Integer, primary_key=True, autoincrement=True)
    EmployeeCode = Column(String(10), nullable=False)
    BasicSalary = Column(Numeric(18, 2), default=0)
    HousingAllowance = Column(Numeric(18, 2), default=0)
    TransportationAllowance = Column(Numeric(18, 2), default=0)
    OtherAllowances = Column(Numeric(18, 2), default=0)
    Deductions = Column(Numeric(18, 2), default=0)
    EffectiveFrom = Column(Date, nullable=False)
    EffectiveTo = Column(Date, nullable=True)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=_utcnow)


class PaySlip(Base):
    __tablename__ = "PaySlip"
    __table_args__ = {"schema": "dbo"}
    PaySlipID = Column(Integer, primary_key=True, autoincrement=True)
    EmployeeCode = Column(String(10), nullable=False)
    PayPeriod = Column(String(20), nullable=False)
    PayDate = Column(Date, nullable=False)
    BasicSalary = Column(Numeric(18, 2), default=0)
    TotalAllowances = Column(Numeric(18, 2), default=0)
    GrossPay = Column(Numeric(18, 2), default=0)
    TotalDeductions = Column(Numeric(18, 2), default=0)
    NetPay = Column(Numeric(18, 2), default=0)
    Status = Column(String(20), default="draft")
    Remarks = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)

    allowances = relationship("Allowance", back_populates="payslip", cascade="all, delete-orphan")
    deductions = relationship("Deduction", back_populates="payslip", cascade="all, delete-orphan")


class Deduction(Base):
    __tablename__ = "Deduction"
    __table_args__ = {"schema": "dbo"}
    DeductionID = Column(Integer, primary_key=True, autoincrement=True)
    PaySlipID = Column(Integer, ForeignKey("dbo.PaySlip.PaySlipID"), nullable=False)
    DeductionType = Column(String(100), nullable=False)
    Amount = Column(Numeric(18, 2), default=0)
    Description = Column(Text, nullable=True)

    payslip = relationship("PaySlip", back_populates="deductions")


class Allowance(Base):
    __tablename__ = "Allowance"
    __table_args__ = {"schema": "dbo"}
    AllowanceID = Column(Integer, primary_key=True, autoincrement=True)
    PaySlipID = Column(Integer, ForeignKey("dbo.PaySlip.PaySlipID"), nullable=False)
    AllowanceType = Column(String(100), nullable=False)
    Amount = Column(Numeric(18, 2), default=0)
    Description = Column(Text, nullable=True)

    payslip = relationship("PaySlip", back_populates="allowances")


class Attendance(Base):
    __tablename__ = "Attendance"
    __table_args__ = {"schema": "dbo"}
    AttendanceID = Column(Integer, primary_key=True, autoincrement=True)
    EmployeeCode = Column(String(10), nullable=False)
    AttendanceDate = Column(Date, nullable=False)
    CheckIn = Column(DateTime, nullable=True)
    CheckOut = Column(DateTime, nullable=True)
    HoursWorked = Column(Numeric(5, 2), default=0)
    Status = Column(String(20), default="present")
    Remarks = Column(Text, nullable=True)
