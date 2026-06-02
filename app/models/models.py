import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class PNRDim(Base):
    __tablename__ = "pnr_dim"
    pnr_id = Column(Integer, primary_key=True, autoincrement=True)
    pnr_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200))
    pnr_type = Column(String(50), default="UNALLOCATED")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ClientDim(Base):
    __tablename__ = "client_dim"
    client_id = Column(Integer, primary_key=True, autoincrement=True)
    client_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(100))
    tax_id = Column(String(50))
    category = Column(String(50))
    status = Column(String(20), default="active")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class VendorDim(Base):
    __tablename__ = "vendor_dim"
    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(100))
    tax_id = Column(String(50))
    category = Column(String(50))
    payment_terms = Column(String(100))
    credit_limit = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class EmployeeDim(Base):
    __tablename__ = "employee_dim"
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    department = Column(String(100))
    position = Column(String(100))
    base_salary = Column(Float, default=0.0)
    hourly_rate = Column(Float, default=0.0)
    overtime_rate = Column(Float, default=0.0)
    phone = Column(String(50))
    email = Column(String(100))
    hire_date = Column(Date)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class EventDim(Base):
    __tablename__ = "event_dim"
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    event_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    event_type = Column(String(50))
    branch = Column(String(100))
    status = Column(String(20), default="draft")
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    trnx_id = Column(Integer, primary_key=True, autoincrement=True)
    source_system = Column(String(20), default="BNK")
    trnx_type = Column(String(50))
    trnx_date = Column(Date)
    value_date = Column(Date)
    description = Column(String(500))
    cheque_no = Column(String(50))
    orignal_amount = Column(Float)
    egp_amount = Column(Float)
    currency = Column(String(10), default="EGP")
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    contra_code = Column(String(50))
    contra_name = Column(String(200))
    pnr_code = Column(String(50))
    pnr_id = Column(Integer, ForeignKey("pnr_dim.pnr_id"))
    allocation_status = Column(String(20), default="unallocated")
    reconciled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"
    inv_id = Column(Integer, primary_key=True, autoincrement=True)
    source_system = Column(String(20), default="EINV_SAL")
    invoice_no = Column(String(50), unique=True, index=True)
    invoice_date = Column(Date)
    client_code = Column(String(50))
    client_name = Column(String(200))
    client_id = Column(Integer, ForeignKey("client_dim.client_id"))
    category = Column(String(100))
    sub_category = Column(String(100))
    orignal_amount = Column(Float)
    egp_amount = Column(Float)
    currency = Column(String(10), default="EGP")
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float)
    status = Column(String(20), default="pending")
    due_date = Column(Date)
    paid_amount = Column(Float, default=0.0)
    pnr_code = Column(String(50))
    pnr_id = Column(Integer, ForeignKey("pnr_dim.pnr_id"))
    allocation_status = Column(String(20), default="unallocated")
    event_id = Column(Integer, ForeignKey("event_dim.event_id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    inv_id = Column(Integer, primary_key=True, autoincrement=True)
    source_system = Column(String(20), default="EINV_PUR")
    invoice_no = Column(String(50), unique=True, index=True)
    invoice_date = Column(Date)
    vendor_code = Column(String(50))
    vendor_name = Column(String(200))
    vendor_id = Column(Integer, ForeignKey("vendor_dim.vendor_id"))
    category = Column(String(100))
    sub_category = Column(String(100))
    orignal_amount = Column(Float)
    egp_amount = Column(Float)
    currency = Column(String(10), default="EGP")
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float)
    status = Column(String(20), default="pending")
    due_date = Column(Date)
    paid_amount = Column(Float, default=0.0)
    pnr_code = Column(String(50))
    pnr_id = Column(Integer, ForeignKey("pnr_dim.pnr_id"))
    allocation_status = Column(String(20), default="unallocated")
    event_id = Column(Integer, ForeignKey("event_dim.event_id"))
    po_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditTrail(Base):
    __tablename__ = "audit_trail"
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer)
    action = Column(String(20), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    changed_by = Column(String(100))
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String(50))


class EmployeeAssignment(Base):
    __tablename__ = "employee_assignments"
    assign_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employee_dim.employee_id"), nullable=False)
    event_id = Column(Integer, ForeignKey("event_dim.event_id"), nullable=False)
    role = Column(String(100))
    hours_worked = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    assignment_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EventPNRAllocation(Base):
    __tablename__ = "event_pnr_allocation"
    alloc_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("event_dim.event_id"), nullable=False)
    pnr_id = Column(Integer, ForeignKey("pnr_dim.pnr_id"), nullable=False)
    allocated_amount = Column(Float, default=0.0)
    allocation_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SubLedgerMaster(Base):
    __tablename__ = "sub_ledger_master"
    sub_ledger_id = Column(Integer, primary_key=True, autoincrement=True)
    sub_ledger_code = Column(String(50), unique=True, index=True)
    name = Column(String(200))
    name_ar = Column(String(200))
    acc_key = Column(String(50))
    sub_leg_code = Column(String(50))
    ledger_type = Column(String(50))
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"
    period_id = Column(Integer, primary_key=True, autoincrement=True)
    period_code = Column(String(20), unique=True)
    year = Column(Integer)
    month = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BudgetLine(Base):
    __tablename__ = "budget_lines"
    budget_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("event_dim.event_id"), nullable=False)
    category = Column(String(100))
    budgeted_amount = Column(Float, default=0.0)
    actual_amount = Column(Float, default=0.0)
    variance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_type = Column(String(20), nullable=False)
    invoice_id = Column(Integer, nullable=False)
    payment_date = Column(Date)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))
    reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ORModuleData(Base):
    __tablename__ = "or_module_data"
    or_id = Column(Integer, primary_key=True, autoincrement=True)
    or_type = Column(String(50))
    or_number = Column(String(50), unique=True, index=True)
    or_date = Column(Date)
    total_amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ALERPMtbl(Base):
    __tablename__ = "al_erp_mtbls"
    mtbl_id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100))
    column_name = Column(String(100))
    column_type = Column(String(50))
    is_pk = Column(Boolean, default=False)
    is_nullable = Column(Boolean, default=True)
    default_value = Column(String(200))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EventCost(Base):
    __tablename__ = "event_costs"
    cost_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("event_dim.event_id"), nullable=False)
    cost_type = Column(String(50))
    amount = Column(Float, default=0.0)
    description = Column(Text)
    cost_date = Column(Date)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class VendorPerformance(Base):
    __tablename__ = "vendor_performance"
    perf_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendor_dim.vendor_id"), nullable=False)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    period = Column(String(20))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ClientSegment(Base):
    __tablename__ = "client_segments"
    segment_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("client_dim.client_id"), nullable=False)
    segment_name = Column(String(100))
    segment_value = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    rate_id = Column(Integer, primary_key=True, autoincrement=True)
    currency_code = Column(String(10), nullable=False)
    rate_to_egp = Column(Float, nullable=False)
    rate_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PNRAllocationSummary(Base):
    __tablename__ = "pnr_allocation_summary"
    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    pnr_id = Column(Integer, ForeignKey("pnr_dim.pnr_id"), nullable=False)
    total_debits = Column(Float, default=0.0)
    total_credits = Column(Float, default=0.0)
    net_balance = Column(Float, default=0.0)
    period = Column(String(20))
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class EventMilestone(Base):
    __tablename__ = "event_milestones"
    milestone_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("event_dim.event_id"), nullable=False)
    milestone_name = Column(String(200))
    planned_date = Column(Date)
    actual_date = Column(Date)
    status = Column(String(20), default="pending")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class NotificationLog(Base):
    __tablename__ = "notification_log"
    notify_id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String(200))
    subject = Column(String(200))
    message = Column(Text)
    channel = Column(String(20))
    status = Column(String(20), default="pending")
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    token = Column(Text, nullable=False)
    role = Column(String(50))
    login_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    ip_address = Column(String(50))
    is_active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════════════
# PIPELINE LOG TABLES (ERP Builder Protocoll v2.1)
# ════════════════════════════════════════════════════════════════

class ExtractionLog(Base):
    __tablename__ = "extraction_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    module = Column(String(20), nullable=False)
    source_file = Column(String(200))
    user_id = Column(String(100))
    status = Column(String(20))
    records_read = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    errors = Column(Text)
    extracted_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ValidationLog(Base):
    __tablename__ = "validation_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    extract_id = Column(Integer, nullable=False)
    user_id = Column(String(100))
    status = Column(String(20))
    quality_score = Column(Float, default=0.0)
    passed_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    rule_results = Column(JSON)
    validated_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class StagingLog(Base):
    __tablename__ = "staging_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    validate_id = Column(Integer, nullable=False)
    target_table = Column(String(50))
    user_id = Column(String(100))
    snapshot_id = Column(String(100))
    status = Column(String(20))
    records_staged = Column(Integer, default=0)
    staged_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ReconcileLog(Base):
    __tablename__ = "reconcile_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(Integer, nullable=False)
    module = Column(String(20))
    user_id = Column(String(100))
    status = Column(String(20))
    total_records = Column(Integer, default=0)
    reconciled_count = Column(Integer, default=0)
    mismatch_count = Column(Integer, default=0)
    unmatched_count = Column(Integer, default=0)
    total_debit = Column(Float, default=0.0)
    total_credit = Column(Float, default=0.0)
    difference = Column(Float, default=0.0)
    reconciled_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ApprovalLog(Base):
    __tablename__ = "approval_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recon_id = Column(Integer, nullable=False)
    approver_id = Column(String(100))
    approval_level = Column(String(20))
    status = Column(String(20))
    approved_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PromotionLog(Base):
    __tablename__ = "promotion_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    approve_id = Column(Integer, nullable=False)
    user_id = Column(String(100))
    rollback_token = Column(String(100))
    status = Column(String(20))
    records_promoted = Column(Integer, default=0)
    promoted_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ObserveLog(Base):
    __tablename__ = "observe_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    promote_id = Column(Integer, nullable=False)
    user_id = Column(String(100))
    status = Column(String(20))
    metrics = Column(Text)
    alert_count = Column(Integer, default=0)
    observed_at = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ════════════════════════════════════════════════════════════════
# STAGING TABLES (Pre-production isolation)
# ════════════════════════════════════════════════════════════════

class BnkStaging(Base):
    __tablename__ = "bnk_staging"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50))
    check_book_id = Column(String(50))
    transaction_date = Column(String(20))
    narration = Column(Text)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    sub_led_code = Column(String(50))
    pnr_id = Column(String(50))
    trnx_type = Column(String(50))
    trnx_ref = Column(String(100))
    _extracted_at = Column(String(50))
    _batch_id = Column(String(50))
    _module = Column(String(10))
    validation_status = Column(String(20), default="PENDING")
    validation_errors = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SalesStaging(Base):
    __tablename__ = "sales_staging"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_no = Column(String(50))
    invoice_date = Column(String(20))
    client_id = Column(String(50))
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    tax_amount = Column(Float, default=0.0)
    sub_led_code = Column(String(50))
    pnr_id = Column(String(50))
    _extracted_at = Column(String(50))
    _batch_id = Column(String(50))
    _module = Column(String(10))
    validation_status = Column(String(20), default="PENDING")
    validation_errors = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PurchaseStaging(Base):
    __tablename__ = "purchase_staging"
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_no = Column(String(50))
    po_date = Column(String(20))
    vendor_id = Column(String(50))
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    tax_amount = Column(Float, default=0.0)
    sub_led_code = Column(String(50))
    pnr_id = Column(String(50))
    _extracted_at = Column(String(50))
    _batch_id = Column(String(50))
    _module = Column(String(10))
    validation_status = Column(String(20), default="PENDING")
    validation_errors = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EventsStaging(Base):
    __tablename__ = "events_staging"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pnr_id = Column(String(50))
    event_date = Column(String(20))
    client_id = Column(String(50))
    gross_sales = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    _extracted_at = Column(String(50))
    _batch_id = Column(String(50))
    _module = Column(String(10))
    validation_status = Column(String(20), default="PENDING")
    validation_errors = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EnvironmentalStaging(Base):
    __tablename__ = "environmental_staging"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50))
    project_date = Column(String(20))
    department = Column(String(100))
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    _extracted_at = Column(String(50))
    _batch_id = Column(String(50))
    _module = Column(String(10))
    validation_status = Column(String(20), default="PENDING")
    validation_errors = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ════════════════════════════════════════════════════════════════
# PRODUCTION TABLES (from migrate_to_real_schema.py)
# ════════════════════════════════════════════════════════════════

class COAMaster(Base):
    __tablename__ = "coa_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_key = Column(String(50), unique=True, index=True)
    acc_name = Column(String(200))
    acc_name_ar = Column(String(200))
    categ_key = Column(String(50))
    acc_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50))
    trnx_num = Column(String(50))
    trnx_date = Column(String(20))
    account_id = Column(String(50))
    acc_name = Column(String(200))
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    sub_led_code = Column(String(50))
    pnr_id = Column(String(50))
    narration = Column(Text)
    status = Column(String(20), default="VALID")
    status_note = Column(Text)
    trnx_ref = Column(String(100))
    trnx_type = Column(String(50))
    currency = Column(String(10), default="EGP")
    batch_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PettyCashRegister(Base):
    __tablename__ = "petty_cash_register"
    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_no = Column(String(50), unique=True, index=True)
    voucher_date = Column(Date)
    description = Column(String(500))
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    paid_to = Column(String(200))
    category = Column(String(100))
    pnr_id = Column(String(50))
    event_id = Column(Integer, ForeignKey("event_dim.event_id"))
    status = Column(String(20), default="pending")
    approved_by = Column(String(100))
    receipt_ref = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ChequeBook(Base):
    __tablename__ = "cheque_books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cheque_no = Column(String(50), unique=True, index=True)
    cheque_date = Column(Date)
    payee = Column(String(200))
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EGP")
    bank_account = Column(String(50))
    status = Column(String(20), default="issued")
    issued_to = Column(String(200))
    pnr_id = Column(String(50))
    event_id = Column(Integer, ForeignKey("event_dim.event_id"))
    notes = Column(Text)
    cleared_date = Column(Date)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WHTRecord(Base):
    __tablename__ = "wht_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    certificate_no = Column(String(50), unique=True, index=True)
    deduction_date = Column(Date)
    vendor_id = Column(Integer, ForeignKey("vendor_dim.vendor_id"))
    gross_amount = Column(Float, default=0.0)
    wht_rate = Column(Float, default=1.0)
    wht_amount = Column(Float, default=0.0)
    invoice_ref = Column(String(100))
    period = Column(String(20))
    status = Column(String(20), default="pending")
    filed_at = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
