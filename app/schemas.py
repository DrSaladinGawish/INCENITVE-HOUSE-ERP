import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PNRDimCreate(BaseModel):
    pnr_code: str
    name: Optional[str] = None
    pnr_type: str = "UNALLOCATED"
    status: str = "active"


class PNRDimUpdate(BaseModel):
    name: Optional[str] = None
    pnr_type: Optional[str] = None
    status: Optional[str] = None


class PNRDimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pnr_id: int
    pnr_code: str
    name: Optional[str] = None
    pnr_type: str
    status: str
    created_at: Optional[datetime.datetime] = None


class ClientCreate(BaseModel):
    client_code: str
    name: str
    name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    category: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    category: Optional[str] = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    client_id: int
    client_code: str
    name: str
    name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    category: Optional[str] = None
    status: str
    is_deleted: bool


class VendorCreate(BaseModel):
    vendor_code: str
    name: str
    name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    category: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: float = 0.0


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    category: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    vendor_id: int
    vendor_code: str
    name: str
    name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    category: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: float
    status: str


class EmployeeCreate(BaseModel):
    employee_code: str
    name: str
    name_ar: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    base_salary: float = 0.0
    hourly_rate: float = 0.0
    overtime_rate: float = 0.0
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[datetime.date] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    base_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    overtime_rate: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[datetime.date] = None
    status: Optional[str] = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    employee_id: int
    employee_code: str
    name: str
    name_ar: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    base_salary: float
    hourly_rate: float
    overtime_rate: float
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[datetime.date] = None
    status: str


class EmployeeAssignmentCreate(BaseModel):
    employee_id: int
    event_id: int
    role: Optional[str] = None
    hours_worked: float = 0.0
    overtime_hours: float = 0.0
    assignment_date: Optional[datetime.date] = None
    notes: Optional[str] = None


class EmployeeAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assign_id: int
    employee_id: int
    event_id: int
    role: Optional[str] = None
    hours_worked: float
    overtime_hours: float
    cost: float
    assignment_date: Optional[datetime.date] = None
    notes: Optional[str] = None


class EventCreate(BaseModel):
    event_code: str
    name: str
    name_ar: Optional[str] = None
    event_type: Optional[str] = None
    branch: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    budget: float = 0.0
    notes: Optional[str] = None


class EventUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    event_type: Optional[str] = None
    branch: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    revenue: Optional[float] = None
    notes: Optional[str] = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: int
    event_code: str
    name: str
    name_ar: Optional[str] = None
    event_type: Optional[str] = None
    branch: Optional[str] = None
    status: str
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    budget: float
    actual_cost: float
    revenue: float
    notes: Optional[str] = None


class SalesInvoiceCreate(BaseModel):
    invoice_no: str
    invoice_date: Optional[datetime.date] = None
    client_code: Optional[str] = None
    client_name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    orignal_amount: float = 0.0
    egp_amount: float = 0.0
    currency: str = "EGP"
    tax_amount: float = 0.0
    total_amount: float = 0.0
    due_date: Optional[datetime.date] = None
    pnr_code: Optional[str] = None


class SalesInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    inv_id: int
    invoice_no: str
    invoice_date: Optional[datetime.date] = None
    client_code: Optional[str] = None
    client_name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    total_amount: float
    status: str
    due_date: Optional[datetime.date] = None
    paid_amount: float
    pnr_code: Optional[str] = None


class PurchaseInvoiceCreate(BaseModel):
    invoice_no: str
    invoice_date: Optional[datetime.date] = None
    vendor_code: Optional[str] = None
    vendor_name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    orignal_amount: float = 0.0
    egp_amount: float = 0.0
    currency: str = "EGP"
    tax_amount: float = 0.0
    total_amount: float = 0.0
    due_date: Optional[datetime.date] = None
    pnr_code: Optional[str] = None
    po_number: Optional[str] = None


class PurchaseInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    inv_id: int
    invoice_no: str
    invoice_date: Optional[datetime.date] = None
    vendor_code: Optional[str] = None
    vendor_name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    total_amount: float
    status: str
    due_date: Optional[datetime.date] = None
    paid_amount: float
    pnr_code: Optional[str] = None
    po_number: Optional[str] = None


class BankTransactionCreate(BaseModel):
    trnx_type: Optional[str] = None
    trnx_date: Optional[datetime.date] = None
    description: Optional[str] = None
    orignal_amount: float = 0.0
    egp_amount: float = 0.0
    currency: str = "EGP"
    debit: float = 0.0
    credit: float = 0.0
    contra_code: Optional[str] = None
    pnr_code: Optional[str] = None


class BankTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    trnx_id: int
    trnx_type: Optional[str] = None
    trnx_date: Optional[datetime.date] = None
    description: Optional[str] = None
    orignal_amount: float
    egp_amount: float
    debit: float
    credit: float
    balance: float
    pnr_code: Optional[str] = None
    allocation_status: str
    reconciled: bool


class AuditTrailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    audit_id: int
    table_name: str
    record_id: Optional[int] = None
    action: str
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    changed_by: Optional[str] = None
    changed_at: Optional[datetime.datetime] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class PNRBulkClassify(BaseModel):
    pnr_ids: list[int]
    pnr_type: str


class PNRAllocationReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pnr_id: int
    pnr_code: str
    pnr_type: str
    total_debits: float = 0.0
    total_credits: float = 0.0
    net_balance: float = 0.0
    sales_count: int = 0
    purchase_count: int = 0
    bank_count: int = 0


class DashboardKPIs(BaseModel):
    total_revenue: float = 0.0
    total_cost: float = 0.0
    profit_margin: float = 0.0
    active_events: int = 0
    pending_invoices: int = 0
    overdue_invoices: int = 0
    bank_balance: float = 0.0


class MonthlyTrend(BaseModel):
    month: str
    revenue: float = 0.0
    cost: float = 0.0
    profit: float = 0.0


class EventPnL(BaseModel):
    event_code: str
    event_name: str
    revenue: float = 0.0
    cost: float = 0.0
    profit: float = 0.0
    margin: float = 0.0


class BalanceSheetItem(BaseModel):
    category: str
    sub_category: str
    amount: float = 0.0
    period: Optional[str] = None


class ReportFilter(BaseModel):
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    pnr_code: Optional[str] = None
    event_code: Optional[str] = None
    limit: int = 100
    offset: int = 0


# ════════════════════════════════════════════════════════════════
# PIPELINE SCHEMAS (ERP Builder Protocol)
# ════════════════════════════════════════════════════════════════

class ExtractRequest(BaseModel):
    module: str
    source_file: Optional[str] = None
    dry_run: bool = False


class ExtractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    module: str
    source_file: Optional[str] = None
    records_read: int = 0
    records_inserted: int = 0
    errors: list = []
    extract_id: Optional[int] = None
    preview: Optional[list] = None


class ValidateRequest(BaseModel):
    extract_id: int


class ValidateResponse(BaseModel):
    status: str
    validate_id: Optional[int] = None
    extract_id: int
    quality_score: float = 0.0
    passed_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    rule_results: list = []


class StageRequest(BaseModel):
    validate_id: int
    target_table: str


class StageResponse(BaseModel):
    status: str
    stage_id: Optional[int] = None
    validate_id: int
    snapshot_id: Optional[str] = None
    target_table: str
    records_staged: int = 0


class ReconcileRequest(BaseModel):
    stage_id: int
    module: str = "BNK"


class ReconcileResponse(BaseModel):
    status: str
    recon_id: Optional[int] = None
    stage_id: int
    module: str
    total_records: int = 0
    reconciled_count: int = 0
    mismatch_count: int = 0
    unmatched_count: int = 0
    total_debit: float = 0.0
    total_credit: float = 0.0
    difference: float = 0.0
    balanced: bool = False


class ApproveRequest(BaseModel):
    recon_id: int
    approval_level: str = "auto"


class ApproveResponse(BaseModel):
    status: str
    approve_id: Optional[int] = None
    recon_id: int
    approval_level: str
    auto_approved: bool = False


class PromoteRequest(BaseModel):
    approve_id: int


class PromoteResponse(BaseModel):
    status: str
    promote_id: Optional[int] = None
    approve_id: int
    rollback_token: Optional[str] = None
    records_promoted: int = 0


class ObserveRequest(BaseModel):
    promote_id: int


class ObserveResponse(BaseModel):
    status: str
    observe_id: Optional[int] = None
    promote_id: int
    metrics: list = []
    alert_count: int = 0


class PipelineStatusResponse(BaseModel):
    status: str
    version: str = "2.2.2"
    stages: dict = {}
    timestamp: str = ""


# ════════════════════════════════════════════════════════════════
# PROTOCOL VALIDATION SCHEMAS
# ════════════════════════════════════════════════════════════════

class ValidationRuleResult(BaseModel):
    rule: str
    passed: bool
    passed_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    details: list = []


# ════════════════════════════════════════════════════════════════
# MISSING MODULE SCHEMAS
# ════════════════════════════════════════════════════════════════

class PettyCashCreate(BaseModel):
    voucher_no: str
    voucher_date: Optional[datetime.date] = None
    description: str
    amount: float = 0.0
    currency: str = "EGP"
    paid_to: Optional[str] = None
    category: Optional[str] = None
    pnr_id: Optional[str] = None
    event_id: Optional[int] = None
    notes: Optional[str] = None


class PettyCashResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    voucher_no: str
    voucher_date: Optional[datetime.date] = None
    description: str
    amount: float
    currency: str
    paid_to: Optional[str] = None
    category: Optional[str] = None
    pnr_id: Optional[str] = None
    event_id: Optional[int] = None
    status: str
    approved_by: Optional[str] = None


class ChequeCreate(BaseModel):
    cheque_no: str
    cheque_date: Optional[datetime.date] = None
    payee: str
    amount: float = 0.0
    currency: str = "EGP"
    bank_account: Optional[str] = None
    pnr_id: Optional[str] = None
    event_id: Optional[int] = None
    notes: Optional[str] = None


class ChequeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cheque_no: str
    cheque_date: Optional[datetime.date] = None
    payee: str
    amount: float
    currency: str
    bank_account: Optional[str] = None
    status: str
    pnr_id: Optional[str] = None
    event_id: Optional[int] = None


class WHTRecordCreate(BaseModel):
    certificate_no: str
    deduction_date: Optional[datetime.date] = None
    vendor_id: int
    gross_amount: float = 0.0
    wht_rate: float = 1.0
    invoice_ref: Optional[str] = None
    period: Optional[str] = None
    notes: Optional[str] = None


class WHTRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    certificate_no: str
    deduction_date: Optional[datetime.date] = None
    vendor_id: int
    gross_amount: float
    wht_rate: float
    wht_amount: float
    invoice_ref: Optional[str] = None
    period: Optional[str] = None
    status: str


class COAAccountCreate(BaseModel):
    acc_key: str
    acc_name: str
    acc_name_ar: Optional[str] = None
    categ_key: Optional[str] = None
    acc_type: Optional[str] = None


class COAAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    acc_key: str
    acc_name: str
    acc_name_ar: Optional[str] = None
    categ_key: Optional[str] = None
    acc_type: Optional[str] = None
    is_active: bool


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: Optional[str] = None
    trnx_num: Optional[str] = None
    trnx_date: Optional[str] = None
    account_id: Optional[str] = None
    acc_name: Optional[str] = None
    debit: float
    credit: float
    sub_led_code: Optional[str] = None
    pnr_id: Optional[str] = None
    narration: Optional[str] = None
    status: str
    currency: str


class JournalVerifyResponse(BaseModel):
    total_debit: float = 0.0
    total_credit: float = 0.0
    difference: float = 0.0
    balanced: bool = False
    entry_count: int = 0
