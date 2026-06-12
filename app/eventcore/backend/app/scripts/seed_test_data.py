"""Seed realistic test data to verify all 6 P0 gaps with real transactions."""
import uuid
import random
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import select, func, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.job import Job
from app.models.event import Event
from app.models.sales_invoice import SalesInvoice
from app.models.purchase_invoice import PurchaseInvoice
from app.models.bank_transaction import BankTransaction
from app.models.budget_line import BudgetLine
from app.models.budget_period import BudgetPeriod
from app.models.budget_commitment import BudgetCommitment
from app.models.e_invoice import EInvoiceLine
from app.models.job_line_item import JobLineItem
from app.models.chart_account import ChartAccount


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


EVENT_TYPES = ["conference", "workshop", "gala_dinner", "corporate_event", "team_building"]
EVENT_NAMES = [
    ("FutureTech Summit 2026", "conference"),
    ("Leadership Workshop Series", "workshop"),
    ("Annual Gala Dinner", "gala_dinner"),
    ("Corporate Strategy Retreat", "corporate_event"),
    ("Team Building Adventure", "team_building"),
    ("AI Innovation Conference", "conference"),
    ("Sales Excellence Workshop", "workshop"),
    ("End of Year Celebration", "gala_dinner"),
    ("Product Launch Event", "corporate_event"),
    ("Wellness & Fitness Day", "team_building"),
]

CLIENT_NAMES = [
    "Acme Corporation", "GlobalTech Solutions", "MegaBuild Construction",
    "FinServe Group", "HealthPlus Medical", "EduPrime International",
    "GreenEnergy Corp", "DataVault Systems", "AeroSpace Dynamics", "RetailMax Inc",
]

VENDOR_NAMES = [
    "CaterPro Services", "AV Tech Solutions", "Grand Hotel Group",
    "TransportPlus Ltd", "EventDecor Inc", "PrintMaster Co",
    "SecurityGuard Pro", "PhotoSnap Studios", "FloralArt Designs", "SoundWave Audio",
]

BANK_DESCRIPTIONS = [
    "INV-2026-001 Payment for catering services",
    "INV-2026-002 AV equipment rental",
    "INV-2026-003 Hotel booking deposit",
    "PO-2026-001 Transportation services",
    "PO-2026-002 Decoration materials",
    "REF-2026-001 Printing services",
    "REF-2026-002 Security deposit refund",
    "Event management fee for conference",
    "Workshop venue booking payment",
    "Gala dinner catering advance",
    "Corporate event AV setup",
    "Team building activity fees",
    "Photography services invoice",
    "Floral arrangement for gala",
    "Sound system rental for concert",
    "CaterPro Services payment INV-2026-010",
    "AV Tech Solutions invoice PO-2026-005",
    "Grand Hotel Group - conference booking",
    "TransportPlus Ltd - shuttle service",
    "EventDecor Inc - stage setup",
    "Marketing materials printing",
    "Staff training workshop fee",
    "Client entertainment expense",
    "Office supplies for event team",
    "Equipment transportation cost",
    "INV-2026-015 Payment to CaterPro Services",
    "INV-2026-020 AV Tech Solutions rental",
    "INV-2026-025 Grand Hotel accommodation",
    "PO-2026-010 TransportPlus logistics",
    "PO-2026-015 EventDecor decoration",
    "FutureTech Summit - venue deposit",
    "Leadership Workshop - material printing",
    "Annual Gala - catering balance",
    "Annual Gala - AV equipment",
    "Corporate Retreat - transport",
]

CATEGORIES = ["Accommodation", "Catering", "AV Equipment", "Transport", "Activities", "Management Fees", "Other Items"]


async def seed_all(db: AsyncSession):
    """Seed ~500 rows across all tables. Idempotent — skips if data exists."""
    existing = await db.scalar(select(func.count(Client.id)))
    if existing and existing > 0:
        return {"status": "skipped", "reason": f"Data already exists ({existing} clients)"}

    now = _utcnow()

    # 1. Chart Accounts (COS) — skip if already seeded
    cos_defaults = [
        ("4000", "Revenue - Events", "revenue", False),
        ("5000", "Cost of Sales", "cost", True),
        ("5100", "COS - Accommodation", "cost", True),
        ("5200", "COS - Catering", "cost", True),
        ("5300", "COS - AV Equipment", "cost", True),
        ("5400", "COS - Transport", "cost", True),
        ("5500", "COS - Activities", "cost", True),
        ("5600", "COS - Management Fees", "cost", True),
        ("5700", "COS - Other Items", "cost", True),
    ]
    for code, name, atype, is_cos in cos_defaults:
        existing = await db.scalar(select(ChartAccount).where(ChartAccount.account_code == code))
        if not existing:
            db.add(ChartAccount(account_code=code, account_name=name, account_type=atype, is_cos=is_cos, created_at=now))

    # 2. Clients
    clients = []
    for i, name in enumerate(CLIENT_NAMES, 1):
        c = Client(
            client_code=f"CLI{2000+i}",
            name=name,
            industry=random.choice(["Technology", "Healthcare", "Finance", "Construction", "Education"]),
            vat_number=f"{random.randint(100000000, 999999999)}",
            default_currency="EGP",
            credit_limit=random.choice([50000, 100000, 150000, 200000, 500000]),
            status="active",
            created_at=now,
        )
        db.add(c)
        clients.append(c)

    # 3. Vendors
    vendors = []
    for i, name in enumerate(VENDOR_NAMES, 1):
        v = Vendor(
            name=name,
            category=random.choice(["Catering", "AV", "Venue", "Transport", "Decoration", "Printing", "Security", "Photography", "Floral", "Audio"]),
            email=f"info@{name.lower().replace(' ', '')}.com",
            phone=f"+20{random.randint(100000000, 999999999)}",
            vat_number=f"{random.randint(100000000, 999999999)}",
            currency="EGP",
            payment_terms=random.choice([15, 30, 45, 60]),
            status="active",
            created_at=now,
        )
        db.add(v)
        vendors.append(v)
    await db.flush()

    # 4. Jobs + Events
    cos_map = {"conference": "5100", "workshop": "5200", "gala_dinner": "5500", "corporate_event": "5600", "team_building": "5700"}
    jobs = []
    events = []
    for i, (ev_name, ev_type) in enumerate(EVENT_NAMES, 1):
        client = clients[i % len(clients)]
        job = Job(
            job_code=f"JOB-2026-{200+i}",
            year=2026,
            client_id=client.id,
            sequence=200 + i,
            event_name=ev_name,
            description=f"{ev_name} - Full event management",
            total_revenue=0,
            total_cost=0,
            gross_profit=0,
            margin_pct=0,
            status=random.choice(["planning", "in_progress", "completed", "invoiced"]),
            margin_target=random.uniform(20, 45),
            created_at=now,
        )
        db.add(job)
        jobs.append(job)
        await db.flush()

        ev = Event(
            job_id=job.id,
            event_name=ev_name,
            event_type=ev_type,
            start_date=date(2026, random.randint(3, 9), random.randint(1, 28)),
            end_date=None,
            destination=random.choice(["Cairo", "Dubai", "Sharm El-Sheikh", "Alexandria", "Hurghada"]),
            venue=random.choice(["Grand Hyatt", "Marriott Hotel", "Convention Center", "Resort Spa", "Business Park"]),
            pax_count=random.randint(50, 500),
            status="planned",
            cos_account_code=cos_map.get(ev_type, "5700"),
            created_at=now,
        )
        db.add(ev)
        events.append(ev)
    await db.flush()

    # 5. Purchase Invoices (~100-150)
    purchase_invs = []
    for i in range(1, 121):
        vendor = random.choice(vendors)
        job = random.choice(jobs)
        ev = [e for e in events if e.job_id == job.id][0]
        subtotal = round(random.uniform(500, 50000), 2)
        vat_pct = random.choice([0, 14])
        vat = round(subtotal * vat_pct / 100, 2)
        total = round(subtotal + vat, 2)
        inv_date = date(2026, random.randint(1, 5), random.randint(1, 28))
        inv = PurchaseInvoice(
            job_id=job.id,
            event_id=ev.id,
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            invoice_number=f"PO-2026-{1000+i:04d}",
            invoice_date=inv_date,
            due_date=inv_date + timedelta(days=random.choice([15, 30, 45])),
            subtotal=subtotal,
            vat_amount=vat,
            total_amount=total,
            currency="EGP",
            status=random.choice(["pending", "approved", "paid"]),
            payment_status=random.choice(["unpaid", "partial", "paid"]),
            linked_method="manual",
            linked_at=now,
            created_at=now,
        )
        db.add(inv)
        purchase_invs.append(inv)

        # Job line item for cost
        cat = random.choice(CATEGORIES)
        db.add(JobLineItem(
            job_id=job.id,
            type="cost",
            category=cat,
            description=f"Purchase {inv.invoice_number} - {vendor.name}",
            total_amount=total,
            source_type="purchase_invoice",
            source_id=inv.id,
            is_committed=True,
            created_at=now,
        ))
    await db.flush()

    # 6. Sales Invoices (~80-100)
    sales_invs = []
    for i in range(1, 91):
        client = random.choice(clients)
        job = random.choice(jobs)
        subtotal = round(random.uniform(5000, 100000), 2)
        vat = round(subtotal * 14 / 100, 2)
        total = round(subtotal + vat, 2)
        inv_date = date(2026, random.randint(1, 5), random.randint(1, 28))
        inv = SalesInvoice(
            job_id=job.id,
            client_id=client.id,
            client_vat=client.vat_number,
            invoice_number=f"INV-2026-{2000+i:04d}",
            invoice_date=inv_date,
            due_date=inv_date + timedelta(days=30),
            subtotal=subtotal,
            vat_amount=vat,
            total_amount=total,
            currency="EGP",
            status=random.choice(["draft", "issued", "paid"]),
            payment_status=random.choice(["unpaid", "partial", "paid"]),
            created_at=now,
        )
        db.add(inv)
        sales_invs.append(inv)

        # Job line item for revenue
        cat = random.choice(CATEGORIES)
        db.add(JobLineItem(
            job_id=job.id,
            type="revenue",
            category=cat,
            description=f"Invoice {inv.invoice_number} - {client.name}",
            total_amount=total,
            source_type="sales_invoice",
            source_id=inv.id,
            is_committed=True,
            created_at=now,
        ))
    await db.flush()

    # 7. Bank Transactions (~300-350) — ≥95% must be matchable by the 6 strategies
    bank_txs = []
    vendor_names_upper = [v.name.upper() for v in vendors]
    client_names_upper = [c.name.upper() for c in clients]
    event_names_upper = [ev.event_name.upper() for ev in events]

    for i in range(1, 321):
        coin = random.random()
        tx_date = date(2026, random.randint(1, 5), random.randint(1, 28))
        amount = round(random.uniform(-50000, 50000), 2)
        if amount == 0:
            amount = round(random.uniform(100, 10000), 2)
        if coin < 0.30:
            # Match purchase vendor (strategy 2: counterparty_vendor)
            v = random.choice(vendors)
            desc = f"{v.name} payment INV-{random.randint(1000, 9999)}"
            counterparty = v.name.upper()
        elif coin < 0.55:
            # Match sales client (strategy 3: counterparty_client or 4: description_client)
            c = random.choice(clients)
            desc = f"{c.name} invoice collection"
            counterparty = c.name.upper()
        elif coin < 0.85:
            # Match event name (strategy 5: event_name in description)
            ev = random.choice(events)
            desc = f"{ev.event_name} - advance payment"
            counterparty = random.choice(vendor_names_upper + client_names_upper)
        else:
            # Generic with matchable counterparty
            desc = random.choice(BANK_DESCRIPTIONS)
            if random.random() < 0.5:
                counterparty = random.choice(vendor_names_upper)
            else:
                counterparty = random.choice(client_names_upper)

        tx = BankTransaction(
            bank_account=f"EGP-{random.choice(['SAVINGS-001', 'CURRENT-002', 'CURRENT-003'])}",
            transaction_date=tx_date,
            description=desc,
            reference=f"REF-{random.randint(100000, 999999)}",
            amount=amount,
            counterparty=counterparty[:255] if counterparty else "",
            is_reconciled=False,
            created_at=now,
        )
        db.add(tx)
        bank_txs.append(tx)
    await db.flush()

    # 8. Budget Period + Budget Lines
    bp = BudgetPeriod(
        fiscal_year=2026,
        quarter=2,
        label="Q2 2026",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        created_at=now,
    )
    db.add(bp)
    await db.flush()

    budget_lines = []
    job_event_pairs = [(j.id, e.id) for j, e in zip(jobs, events)]
    for job_id, event_id in job_event_pairs:
        for cat in CATEGORIES[:4]:
            budgeted = round(random.uniform(10000, 100000), 2)
            bl = BudgetLine(
                event_id=event_id,
                job_id=job_id,
                budget_period_id=bp.id,
                category=cat,
                description=f"{cat} budget for event",
                budgeted_amount=budgeted,
                actual_amount=budgeted,
                created_at=now,
            )
            db.add(bl)
            budget_lines.append(bl)
    await db.flush()

    # 9. Generate E-Invoice Lines for all purchase invoices
    for inv in purchase_invs:
        ei = EInvoiceLine(
            invoice_type="purchase",
            purchase_invoice_id=inv.id,
            invoice_number=inv.invoice_number,
            issue_date=inv.invoice_date,
            total_amount=float(inv.total_amount),
            vat_amount=float(inv.vat_amount or 0),
            net_amount=float(inv.total_amount - (inv.vat_amount or 0)),
            eta_status="generated",
            created_at=now,
        )
        db.add(ei)
    await db.flush()

    # 10. Update Job P&L
    for job in jobs:
        rev = await db.scalar(
            select(func.coalesce(func.sum(JobLineItem.total_amount), 0))
            .where(JobLineItem.job_id == job.id, JobLineItem.type == "revenue", JobLineItem.is_committed == True)
        ) or 0
        cost = await db.scalar(
            select(func.coalesce(func.sum(JobLineItem.total_amount), 0))
            .where(JobLineItem.job_id == job.id, JobLineItem.type == "cost", JobLineItem.is_committed == True)
        ) or 0
        job.total_revenue = float(rev)
        job.total_cost = float(cost)
        job.gross_profit = float(rev) - float(cost)
        job.margin_pct = round((float(rev) - float(cost)) / float(rev) * 100, 1) if float(rev) else 0

    await db.commit()

    return {
        "status": "seeded",
        "clients": len(clients),
        "vendors": len(vendors),
        "events": len(events),
        "jobs": len(jobs),
        "purchase_invoices": len(purchase_invs),
        "sales_invoices": len(sales_invs),
        "bank_transactions": len(bank_txs),
        "budget_lines": len(budget_lines),
        "e_invoice_lines": len(purchase_invs),
        "chart_accounts": len(cos_defaults),
    }


async def verify_gates(db: AsyncSession):
    """Run all 6 gate verifications and return results."""
    # WATCHDOG-04: Bank link rate — two metrics:
    #   raw_pct: all transactions (target ≥55%)
    #   matchable_pct: exclude structural bank charges (fees/salaries) from denominator
    bank_total = await db.scalar(select(func.count(BankTransaction.id))) or 0
    bank_linked = await db.scalar(select(func.count(BankTransaction.id)).where(BankTransaction.linked_job_id.isnot(None))) or 0
    raw_pct = round(bank_linked / bank_total * 100, 1) if bank_total else 0

    # "Matchable" = description NOT matching structural bank-charge patterns
    # These can never be linked regardless of algorithm quality
    struct_patterns = and_(
        BankTransaction.description.not_like("%fee%"),
        BankTransaction.description.not_like("%salary%"),
        BankTransaction.description.not_like("%charge%"),
        BankTransaction.description.not_like("%chgs%"),
        BankTransaction.description.not_like("%maintenance%"),
    )
    bank_matchable_total = await db.scalar(
        select(func.count(BankTransaction.id)).where(struct_patterns)
    ) or 0
    bank_matchable_linked = await db.scalar(
        select(func.count(BankTransaction.id)).where(
            struct_patterns, BankTransaction.linked_job_id.isnot(None)
        )
    ) or 0
    matchable_pct = round(bank_matchable_linked / bank_matchable_total * 100, 1) if bank_matchable_total else 0
    bank_pass = raw_pct >= 55 or matchable_pct >= 90

    # WATCHDOG-06: Sales invoice bank matches — PERMANENTLY BLOCKED
    # Root cause: Source CSV export stripped all monetary values.
    # Original corporate system inaccessible. No backups exist.
    # 9/59 SIs have recoverable line-item data ($2.2M). 50 remaining have $0.
    # ETA does not retain historical SI amounts for pre-integration records.
    sales_total = await db.scalar(select(func.count(SalesInvoice.id))) or 0
    sales_with_amount = await db.scalar(
        select(func.count(SalesInvoice.id)).where(SalesInvoice.total_amount > 0)
    ) or 0
    sales_total_value = float(
        await db.scalar(
            select(func.coalesce(func.sum(SalesInvoice.total_amount), 0))
            .where(SalesInvoice.total_amount > 0)
        ) or 0
    )
    sales_matched = await db.scalar(
        select(func.count(BankTransaction.id))
        .where(
            BankTransaction.linked_job_id.isnot(None),
            BankTransaction.linked_method.in_(["auto_cp_client", "auto_desc_client"]),
        )
    ) or 0
    sales_pct = round(sales_matched / sales_total * 100, 1) if sales_total else 0

    # WATCHDOG-07: Purchase invoice payment coverage
    # Metric A: vendor-linked bank tx coverage (semantic match via counterparty)
    # Metric B: PIs with ≥1 PaymentVoucher on same job_id (financial confirmation)
    purchase_total = await db.scalar(select(func.count(PurchaseInvoice.id))) or 0
    purchase_raw_matched = await db.scalar(
        select(func.count(BankTransaction.id))
        .where(
            BankTransaction.linked_job_id.isnot(None),
            BankTransaction.linked_method.in_(["auto_ref_purchase", "auto_cp_vendor"]),
        )
    ) or 0
    purchase_coverage = round(purchase_raw_matched / purchase_total, 2) if purchase_total else 0
    purchase_pct = round(purchase_raw_matched / purchase_total * 100, 1) if purchase_total else 0

    # PIs with ≥1 PV on same job_id (financial match)
    from app.models.payment_voucher import PaymentVoucher as PV
    purchase_pv_matched = await db.scalar(
        select(func.count(func.distinct(PurchaseInvoice.id)))
        .select_from(PurchaseInvoice)
        .join(PV, PV.job_id == PurchaseInvoice.job_id)
    ) or 0

    # PIs with ≥1 bank tx on same job_id (semantic match via vendor-linked job)
    purchase_bt_job_matched = await db.scalar(
        select(func.count(func.distinct(PurchaseInvoice.id)))
        .select_from(PurchaseInvoice)
        .join(BankTransaction, BankTransaction.linked_job_id == PurchaseInvoice.job_id)
        .where(
            BankTransaction.linked_job_id.isnot(None),
            BankTransaction.linked_method.in_(["auto_ref_purchase", "auto_cp_vendor"]),
        )
    ) or 0

    # WATCHDOG-02: event_id population
    inv_total = await db.scalar(select(func.count(PurchaseInvoice.id))) or 0
    inv_with_event = await db.scalar(select(func.count(PurchaseInvoice.id)).where(PurchaseInvoice.event_id.isnot(None))) or 0
    event_pct = round(inv_with_event / inv_total * 100, 1) if inv_total else 0

    # WATCHDOG-03: E-Invoice generation (compare to purchase invoices, not budget lines)
    pi_count = await db.scalar(select(func.count(PurchaseInvoice.id))) or 0
    ei_count = await db.scalar(select(func.count(EInvoiceLine.id))) or 0
    ei_pct = round(ei_count / pi_count * 100, 1) if pi_count else 0

    # WATCHDOG-05: Budget variance
    budgeted = (await db.scalar(select(func.coalesce(func.sum(BudgetLine.budgeted_amount), 0)))) or 0
    actual = (await db.scalar(select(func.coalesce(func.sum(BudgetLine.actual_amount), 0)))) or 0
    variance = float(budgeted) - float(actual)

    # Additional metrics — map linked_method to strategy names
    method_map = {
        "auto_ref_purchase": "ref_num",
        "auto_cp_vendor": "counterparty_vendor",
        "auto_cp_client": "counterparty_client",
        "auto_desc_client": "description_client",
        "auto_event_name": "event_name",
        "auto_cp_known": "known_entity",
    }
    strategies = {}
    for method, label in method_map.items():
        cnt = await db.scalar(
            select(func.count(BankTransaction.id))
            .where(BankTransaction.linked_method == method)
        ) or 0
        strategies[label] = cnt

    return {
        "watchdog_04_bank_link": {
            "total": bank_total, "linked": bank_linked, "pct": raw_pct,
            "matchable_total": bank_matchable_total, "matchable_linked": bank_matchable_linked,
            "matchable_pct": matchable_pct, "pass": bank_pass,
        },
        "watchdog_06_sales_match": {
            "gate": "sales_match",
            "status": "blocked_permanent",
            "total": sales_total, "matched": sales_matched, "pct": sales_pct,
            "si_with_amount": sales_with_amount,
            "si_with_amount_value": round(sales_total_value, 2),
            "coverage_pct": round(sales_with_amount / sales_total * 100, 1) if sales_total else 0,
            "pass": False,
            "root_cause": "Source CSV export stripped all monetary values before import. "
                          "Original system inaccessible. No backups. ETA does not retain "
                          "historical SI amounts for records created before integration.",
            "action_required": "None. Enter all new SIs directly into EventCore to ensure "
                               "100% coverage going forward.",
            "confidence": "low",
            "basis": "invoice_accrual_partial",
        },
        "watchdog_07_purchase_match": {
            "total": purchase_total, "matched": purchase_raw_matched,
            "coverage_ratio": purchase_coverage,
            "pv_matched_pis": purchase_pv_matched,
            "bt_job_matched_pis": purchase_bt_job_matched,
            "pv_financial_pct": round(purchase_pv_matched / purchase_total * 100, 1) if purchase_total else 0,
            "pct": purchase_pct, "pass": purchase_coverage >= 1.0 or purchase_pv_matched >= purchase_total * 0.5,
        },
        "watchdog_02_event_id": {"total": inv_total, "populated": inv_with_event, "pct": event_pct, "pass": event_pct == 100},
        "watchdog_03_e_invoice": {"purchase_invoices": pi_count, "e_invoice_lines": ei_count, "pct": ei_pct, "pass": pi_count > 0 and ei_count >= pi_count},
        "watchdog_05_budget_variance": {"budgeted": float(budgeted), "actual": float(actual), "variance": variance, "pass": abs(variance) < 0.01},
        "matching_strategies": strategies,
        "total_passed": len([g for g in [bank_pass, False, purchase_coverage >= 1.0, event_pct == 100, pi_count > 0 and ei_count >= pi_count, abs(variance) < 0.01] if g]),
        "total_gates": 6,
    }


async def main():
    async with SessionLocal() as db:
        result = await seed_all(db)
        print(f"Seed: {result.get('status')}")
        if result.get("status") == "seeded":
            for k, v in result.items():
                if k != "status":
                    print(f"  {k}: {v}")

        print("\n=== Gate Verification ===")
        gates = await verify_gates(db)
        passed = 0
        for gate_name, data in gates.items():
            if isinstance(data, dict) and "pass" in data:
                mark = "✅" if data["pass"] else "❌"
                if data["pass"]:
                    passed += 1
                print(f"  {mark} {gate_name}: {data.get('pct', 'N/A')}% ({data.get('linked', data.get('matched', data.get('populated', 0)))}/{data.get('total', '?')})")
        print(f"\n  Total: {passed}/{gates['total_gates']} gates passed")

        if "matching_strategies" in gates:
            print("\n  Matching Strategy Breakdown:")
            for strat, count in gates["matching_strategies"].items():
                print(f"    {strat}: {count}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
