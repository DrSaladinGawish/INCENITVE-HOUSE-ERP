# IHE-ERP Migration Package v3.0

Standalone database migration package for IncentiveHouse ERP.
Requires SQL Server with ODBC Driver 17+.

## Quick Start

1. Copy `.env.example` to `.env` and fill in SQL Server credentials
2. Place data files in the configured paths (see each migration script for required files)
3. Run `RUN_MIGRATIONS.bat`

## Migration Order

| Step | Script | Description |
|------|--------|-------------|
| DDL  | `sql/00_Schema_DDL.sql` | Create 19 IHE base tables |
| DDL  | `sql/07_Neural_AI_Tables.sql` | Create 5 neural tables + seed 4 nodes |
| DDL  | `sql/08_Document_System.sql` | Create 2 document tables |
| 1    | `01_master_loader.py` | Load master data from `Data_Base_Mtbls.xlsx` |
| 2    | `02_bank_loader.py` | Load bank transactions from `Bnk_TRNX SOURCE.xlsx` |
| 3    | `03_gl_loader.py` | Load Gen_Led CSVs into journal vouchers |
| 4    | `04_document_ingest.py` | Batch ingest archived files by SHA-256 |
| 5    | `05_neural_seeder.py` | Populate neural feature store from production data |
| 6    | `06_verify.py` | Post-migration verification (exit 0 = pass) |
| 99   | `99_rollback.py` | Emergency rollback with backup tables |

## Required Source Files

- `Data_Base_Mtbls.xlsx` (13 sheets: Clients, Vendors, Chart_of_Accounts, Currency, Staff, Budget_Lines)
- `Bnk_TRNX SOURCE.xlsx` (bank transactions)
- `Gen_Led_Bnk.csv`, `Gen_Led_SAL.csv`, `Gen_Led_PUR.csv` (general ledger exports)
- Archive directory for document ingest (`ARCHIVE_ROOT` env var)

## Table Inventory (26 total)

**19 IHE tables**: Currency, Client, Vendor, Employee, Bank, ServiceMainCategory,
ServiceSubCategory, ServiceType, ChartOfAccounts, PNRMaster, ClientEmployee,
PNRBudgetLineItem, SalesInvoice, SalesInvoiceLine, PurchaseVoucher,
PurchaseVoucherLine, BankTransaction, JournalVoucher, JournalVoucherLine

**5 Neural tables**: NeuralNode, NeuralPrediction, NeuralFeatureStore,
NeuralTrainingHistory, NeuralMemory

**2 Document tables**: DocumentModule, SupportingDocument

## Rollback

```bash
python migrations/99_rollback.py --full    # Rollback ALL tables with backup
python migrations/99_rollback.py --tables dbo.Client dbo.Vendor  # Selective
```
