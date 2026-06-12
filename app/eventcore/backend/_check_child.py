import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
checks = [
    ("sales_invoice_line_items", "COUNT(*)", None),
    ("sales_invoice_line_items", "COUNT(DISTINCT invoice_id)", None),
    ("sales_invoice_line_items", "SUM(total_amount)", None),
    ("job_line_items", "COUNT(*)", "WHERE source_type='purchase_invoice'"),
    ("job_line_items", "COUNT(DISTINCT source_id)", "WHERE source_type='purchase_invoice'"),
    ("job_line_items", "SUM(total_amount)", "WHERE source_type='purchase_invoice'"),
    ("purchase_invoices", "COUNT(*)", "WHERE payment_voucher_id IS NOT NULL"),
]
for t, agg, cond in checks:
    cond = f" {cond}" if cond else ""
    sql = f"SELECT {agg} FROM {t}{cond}"
    r = c.execute(sql).fetchone()[0]
    print(f"{agg:40} {t:30}{cond:40} = {r}")
