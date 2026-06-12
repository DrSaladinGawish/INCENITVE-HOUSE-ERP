# EventCore ERP — Incentive House of Egypt

Job P&L-centric Event Management ERP for Incentive House of Egypt.

## Architecture

```
┌─────────────────────┐         HTTP/API          ┌─────────────────────┐
│   eventmanager-erp  │  ◄────────────────────►  │     BIO_ERP v5      │
│   (Port 80/8000)    │    BIO Bridge calls     │   (Port 8000)       │
└─────────────────────┘                         └─────────────────────┘
```

## Quick Start

```bash
docker compose up -d
```

Open http://localhost

## Modules

1. **Dashboard** — Agency-wide Job P&L, margin health, cash position
2. **Quotations** — Client brief → Quote → Approval → Job code creation
3. **Work Orders** — Approved quote → Job code generator (YY.CCCCC.NNN)
4. **Sales Invoicing** — ETA portal sales CSV export
5. **Purchasing** — Supplier invoices with FORCED job linking
6. **Bank & Treasury** — Bank reconciliation with drag-drop job assignment
7. **Petty Cash** — Job-tagged expenses before reimbursement
8. **Job P&L** — Revenue - Cost = Profit per job (THE CENTERPIECE)
9. **Reports** — VAT returns, margin analysis, client profitability
10. **BIO Bridge** — Vendor directory, PO approval, GL sync, HR link

## Brand Identity

- **Colors**: Navy #1B2A4A, Gold #C9A84C, Silver #8A8A8A
- **Fonts**: Playfair Display (serif), Inter (sans), Roboto Mono (mono)
- **Tagline**: "The EVENTailors..." — italic, gold, always present
- **Footer**: Egypt + UAE offices, www.incentivehouse.me

## Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
