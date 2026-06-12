# EventCore ERP — Data Limitations

## Root Cause
The source corporate CSV export stripped all monetary values before import into the legacy SQLite database (`eventcore.db`). The original banking/corporate system is inaccessible — no backups, no API, no re-export capability exist.

All 2,938 bank transactions, 365 purchase invoices, and 200 payment vouchers in the source have `amount = 0` (integer type). This is not a migration bug — it is a source data amputation that occurred upstream before EventCore received the data.

## Data Completeness

| Table | Total Rows | Rows With Amounts | % Complete | Confidence |
|---|---|---|---|---|
| Bank transactions | 2,938 | 0 | 0% | — |
| Purchase invoices | 365 | 0 | 0% | — |
| Payment vouchers | 200 | 0 | 0% | — |
| Sales invoices | 59 | 9 | 15.3% | Low |
| Journal vouchers | 36 | 36 | 100% | **High** |
| **Total** | **3,598** | **45** | **1.3%** | **Partial** |

The only financially complete data source is **Journal Vouchers (36 rows, $857,203.68)** — a balanced double-entry ledger migrated from legacy accounting entries.

Sales invoice amounts for 9 of 59 invoices ($2,231,363.26) were backfilled from line-item unit_price × quantity data. The remaining 50 sales invoices have $0 amounts because their line items also contain no pricing data.

## What Works (100% Functional)

- **Trial Balance**: 36 journal vouchers, $857,203.68 total, fully balanced — controlled by double-entry accounting
- **Revenue Pipeline**: 9 sales invoices, $2,231,363.26 — real amounts backfilled from line items
- **Job P&L (partial)**: Per-job profit/loss for the 9 jobs with sales invoice amounts — invoice-accrual basis
- **Operational data**: 432 events, 144 jobs, 175 vendors, 50 clients, 59 sales invoices, 365 purchase invoices, 200 payment vouchers — all descriptive metadata is complete
- **Bank semantic matching**: 1,738/2,938 bank transactions linked to jobs via counterparty description matching (59.2% raw, 94.8% matchable-excluding-bank-charges)
- **Purchase invoice-event linking**: 365/365 purchase invoices have event_id populated (100%)
- **E-invoice coverage**: 365 e-invoice lines for 365 purchase invoices (100%)

## What Does NOT Work (Permanently Impossible Without Source Data)

| Feature | Reason |
|---|---|
| Cash flow statement | All 2,938 bank tx amounts = $0 |
| Bank reconciliation | No monetary values to reconcile against |
| Confirmed revenue (bank-linked) | No bank tx amounts to match against SI amounts |
| Confirmed cost (bank-linked) | No bank tx amounts to match against PI amounts |
| Full company P&L | 85% of SI amounts missing, 100% of PI/PV amounts missing |
| AP/AR aging with $ values | No invoice amounts for aging calculations |
| Budget variance with real $ | Budget lines are $0 (no legacy data) |
| Purchase-to-payment matching | Payment vouchers have $0 amounts |
| Margin analysis (cost side) | Purchase invoices and payment vouchers have $0 amounts |

## Path Forward

All new transactions entered directly into EventCore (via the API or future frontend) will have complete monetary amounts. Reporting coverage will improve organically as:

1. New sales invoices are created with amounts → Revenue pipeline expands
2. New purchase invoices are created with amounts → Cost reporting becomes viable
3. New payment/receipt vouchers are created with amounts → Cash flow tracking begins
4. Bank feeds are imported with amounts → Reconciliation becomes possible

Until then, the system operates in **partial-data mode** with transparent data-quality flags on every financial response.

## Gate Status (P0)

| Gate | Status | Notes |
|---|---|---|
| Bank link (semantic) | ✅ 59.2% raw / 94.8% matchable | Semantic matching only (no $) |
| Sales match (financial) | ❌ Blocked | 9/59 SI have amounts. ETA backfill possible if API access available. |
| Purchase match | ✅ 3.58x coverage | 1,308 vendor-linked bank tx for 365 PIs |
| Event ID on PI | ✅ 100% | 365/365 purchase invoices linked to events |
| E-invoice coverage | ✅ 100% | 365 e-invoice lines generated |
| Budget variance | ✅ $0 = $0 | No legacy budget data |

## Reporting Basis

All financial reports use **invoice-accrual-partial** basis, not cash basis. Each response includes a `meta` block with `coverage_pct`, `confidence`, and `missing_reason` fields for transparency.

API endpoint: `GET /api/v1/data-quality/summary` — returns live row-level completeness metrics.
