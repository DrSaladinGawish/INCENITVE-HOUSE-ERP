"""Initial schema for EventCore ERP

Revision ID: 0001
Revises:
Create Date: 2026-05-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_code", sa.String(10), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100)),
        sa.Column("vat_number", sa.String(50)),
        sa.Column("default_currency", sa.String(3), server_default="EGP"),
        sa.Column("credit_limit", sa.Numeric(15, 2), server_default="0"),
        sa.Column("payment_terms", sa.Integer, server_default="30"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bio_vendor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column("contact_person", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("vat_number", sa.String(50)),
        sa.Column("bank_account", sa.String(100)),
        sa.Column("bank_name", sa.String(100)),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("payment_terms", sa.Integer, server_default="30"),
        sa.Column("rating", sa.Numeric(3, 2)),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bio_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="user"),
        sa.Column("department", sa.String(50)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "cost_centers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(10), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True)),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_code", sa.String(20), unique=True, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("event_dates", postgresql.DATERANGE),
        sa.Column("description", sa.Text),
        sa.Column("total_revenue", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_cost", sa.Numeric(15, 2), server_default="0"),
        sa.Column("gross_profit", sa.Numeric(15, 2), server_default="0"),
        sa.Column("margin_pct", sa.Numeric(5, 2), server_default="0"),
        sa.Column("status", sa.String(20), server_default="planning"),
        sa.Column("margin_target", sa.Numeric(5, 2), server_default="35.0"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_jobs_client", "jobs", ["client_id"])
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_code", "jobs", ["job_code"])

    op.create_table(
        "job_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), server_default="1"),
        sa.Column("unit_price", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("source_type", sa.String(50)),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("client_invoice_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_committed", sa.Boolean, server_default="false"),
        sa.Column("is_locked", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_jli_job", "job_line_items", ["job_id"])
    op.create_index("idx_jli_type", "job_line_items", ["type"])

    op.create_table(
        "purchase_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id")),
        sa.Column("vendor_name", sa.String(255), nullable=False),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("vat_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("exchange_rate", sa.Numeric(10, 6), server_default="1"),
        sa.Column("eta_doc_id", sa.String(100)),
        sa.Column("eta_csv_row", sa.Integer),
        sa.Column("eta_imported_at", sa.DateTime),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("payment_status", sa.String(20), server_default="unpaid"),
        sa.Column("pdf_path", sa.String(500)),
        sa.Column("payment_voucher_id", postgresql.UUID(as_uuid=True)),
        sa.Column("linked_by", postgresql.UUID(as_uuid=True)),
        sa.Column("linked_at", sa.DateTime),
        sa.Column("linked_method", sa.String(20), server_default="manual"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_pi_job", "purchase_invoices", ["job_id"])
    op.create_index("idx_pi_vendor", "purchase_invoices", ["vendor_id"])
    op.create_index("idx_pi_status", "purchase_invoices", ["status"])

    op.create_table(
        "bank_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id")),
        sa.Column("bank_account", sa.String(100), nullable=False),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("reference", sa.String(255)),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("counterparty", sa.String(255)),
        sa.Column("counterparty_account", sa.String(100)),
        sa.Column("is_reconciled", sa.Boolean, server_default="false"),
        sa.Column("reconciled_at", sa.DateTime),
        sa.Column("reconciled_by", postgresql.UUID(as_uuid=True)),
        sa.Column("linked_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id")),
        sa.Column("linked_at", sa.DateTime),
        sa.Column("linked_by", postgresql.UUID(as_uuid=True)),
        sa.Column("linked_method", sa.String(20)),
        sa.Column("match_confidence", sa.Numeric(5, 2)),
        sa.Column("match_reason", sa.Text),
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("raw_csv_row", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_bt_job", "bank_transactions", ["job_id"])
    op.create_index("idx_bt_date", "bank_transactions", ["transaction_date"])
    op.create_index("idx_bt_recon", "bank_transactions", ["is_reconciled"])

    op.create_table(
        "petty_cash",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True)),
        sa.Column("staff_name", sa.String(255), nullable=False),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("has_receipt", sa.Boolean, server_default="false"),
        sa.Column("receipt_path", sa.String(500)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime),
        sa.Column("reimbursed_at", sa.DateTime),
        sa.Column("reimbursement_method", sa.String(20)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_pc_job", "petty_cash", ["job_id"])
    op.create_index("idx_pc_status", "petty_cash", ["status"])

    op.create_table(
        "quotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("quote_number", sa.String(50), unique=True, nullable=False),
        sa.Column("quote_date", sa.Date, nullable=False),
        sa.Column("valid_until", sa.Date),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("event_dates", postgresql.DATERANGE),
        sa.Column("destination", sa.String(255)),
        sa.Column("pax_count", sa.Integer),
        sa.Column("subtotal", sa.Numeric(15, 2), server_default="0"),
        sa.Column("vat_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("converted_to_job_id", postgresql.UUID(as_uuid=True)),
        sa.Column("converted_at", sa.DateTime),
        sa.Column("pdf_path", sa.String(500)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "quotation_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quotation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), server_default="1"),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("vendor_estimate", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column("sort_order", sa.Integer, server_default="0"),
    )

    op.create_table(
        "sales_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("eta_doc_id", sa.String(100)),
        sa.Column("eta_csv_row", sa.Integer),
        sa.Column("eta_imported_at", sa.DateTime),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("client_vat", sa.String(50)),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("vat_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("eta_prod_name", sa.String(255)),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("payment_status", sa.String(20), server_default="unpaid"),
        sa.Column("collected_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("collected_date", sa.Date),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_si_job", "sales_invoices", ["job_id"])
    op.create_index("idx_si_client", "sales_invoices", ["client_id"])

    op.create_table(
        "payment_vouchers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("voucher_number", sa.String(50), unique=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id")),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id")),
        sa.Column("purchase_invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchase_invoices.id")),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EGP"),
        sa.Column("payment_method", sa.String(20)),
        sa.Column("bank_account", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("pdf_path", sa.String(500)),
        sa.Column("pdf_page_count", sa.Integer),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "activity_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id")),
        sa.Column("old_values", postgresql.JSONB),
        sa.Column("new_values", postgresql.JSONB),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_al_job", "activity_log", ["job_id"])
    op.create_index("idx_al_user", "activity_log", ["user_id"])
    op.create_index("idx_al_created", "activity_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("activity_log")
    op.drop_table("payment_vouchers")
    op.drop_table("sales_invoices")
    op.drop_table("quotation_line_items")
    op.drop_table("quotations")
    op.drop_table("petty_cash")
    op.drop_table("bank_transactions")
    op.drop_table("purchase_invoices")
    op.drop_table("job_line_items")
    op.drop_table("jobs")
    op.drop_table("cost_centers")
    op.drop_table("users")
    op.drop_table("vendors")
    op.drop_table("clients")
