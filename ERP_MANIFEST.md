# ERP SYSTEM MANIFEST
# Last Updated: 2026-06-12
# DO NOT MODIFY WITHOUT UPDATING THIS FILE

## System: IncentiveHouse-ERP

### Active Modules (LOCKED — Do not rebuild)
| Module | Status | Files | Last Verified |
|--------|--------|-------|---------------|
| Core Auth | ✅ Complete | app/routers/auth_router.py, app/schemas/auth.py, app/auth.py | 2026-06-12 |
| Sales | ✅ Complete | app/routers/sal_router.py, app/services/sal_service.py, app/schemas/sal.py, app/templates/sales_form.html, app/templates/sales_list.html | 2026-06-12 |
| Purchases | ✅ Complete | app/routers/pur_router.py, app/services/pur_service.py, app/schemas/pur.py, app/templates/purchases_form.html, app/templates/purchases_list.html | 2026-06-12 |
| Banking | ✅ Complete | app/routers/bnk_router.py, app/services/bnk_service.py, app/schemas/bnk.py, app/templates/banking_form.html, app/templates/banking_list.html | 2026-06-12 |
| GL | ✅ Complete | app/routers/gl_router.py, app/services/gl_service.py, app/schemas/gl.py, app/templates/gl_form.html, app/templates/gl_list.html | 2026-06-12 |
| Events/PNR | ✅ Complete | app/routers/evn_router.py, app/services/evn_service.py, app/schemas/evn.py, app/templates/pnr_form.html, app/templates/pnr_list.html, app/templates/pnr_detail.html | 2026-06-12 |
| Meta Layer | ✅ Complete | app/meta_layer/, app/routers/meta_router.py, app/static/meta/, app/templates/meta/ | 2026-06-12 |
| VAT Engine | ✅ Complete | app/static/meta/meta_vat.js | 2026-06-12 |
| Document System | ✅ Complete | app/routers/documents.py, app/services/document/document_service.py, app/models/document/ | 2026-06-12 |
| Dashboard | ✅ Complete | app/routers/dashboard_router.py, app/services/dashboard_service.py, app/templates/dashboard.html | 2026-06-12 |
| AI/Intelligence | ✅ Complete | app/routers/ai_router.py, app/routers/intelligence_router.py, app/services/ai/llm_service.py | 2026-06-12 |
| Export | ✅ Complete | app/routers/export_router.py | 2026-06-12 |
| Neural | ✅ Complete | app/routers/neural/, app/services/neural/, app/models/neural/ | 2026-06-12 |
| Financial Reports | ✅ Complete | app/routers/financial_reports.py, app/services/financial_reports_service.py, app/templates/reports/financial/ | 2026-06-12 |
| E-Invoice XML | ✅ Complete | app/routers/e_invoice.py, app/services/e_invoice_service.py, app/templates/e_invoice/ | 2026-06-12 |
| Workflow Engine | ✅ Complete | app/routers/workflow.py, app/services/workflow_service.py, app/models/workflow_models.py, app/templates/workflow/ | 2026-06-12 |

### Scaffolding Generated (LOCKED — Full CRUD exists)
| Module | Files | Location |
|--------|-------|----------|
| Inventory | 6 files | app/routers/inventory.py, app/services/inventory_service.py, app/models/inventory.py, app/schemas/inventory.py, app/templates/inventory_form.html, app/templates/inventory_list.html |
| Payroll | 6 files | app/routers/payroll.py, app/services/payroll_service.py, app/models/payroll.py, app/schemas/payroll.py, app/templates/payroll_form.html, app/templates/payroll_list.html |
| CRM | 6 files | app/routers/crm.py, app/services/crm_service.py, app/models/crm.py, app/schemas/crm.py, app/templates/crm_lead_form.html, app/templates/crm_leads_list.html |
| Budgeting | 6 files | app/routers/budgeting.py, app/services/budgeting_service.py, app/models/budgeting.py, app/schemas/budgeting.py, app/templates/budget_form.html, app/templates/budgets_list.html |
| Fixed Assets | 6 files | app/routers/fixed_assets.py, app/services/fixed_assets_service.py, app/models/fixed_assets.py, app/schemas/fixed_assets.py, app/templates/asset_form.html, app/templates/assets_list.html |

### In Progress (DO NOT OVERWRITE)
| Feature | Assigned | Started | Blockers |
|---------|----------|---------|----------|

### Global Rules
1. NEVER regenerate a module marked ✅ Complete
2. NEVER modify a file without checking this manifest first
3. ALWAYS append to this manifest when adding new files
4. ALWAYS verify with `git diff` before committing
5. Last git tag: v2.4.0 (99 tests, 20 pages)
