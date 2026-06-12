import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
# Check job_line_items source_type values
r = c.execute("SELECT source_type, COUNT(*) FROM job_line_items WHERE source_type IS NOT NULL GROUP BY source_type").fetchall()
print("job_line_items source_type:", r)
# Check if any purchase invoices have related data
r2 = c.execute("SELECT COUNT(*) FROM job_line_items WHERE source_type='purchase_invoice' AND source_id IS NOT NULL").fetchone()
print("Purchase invoice linked JLI:", r2[0])
# Sales_invoice_line_items with amounts
r3 = c.execute("SELECT COUNT(DISTINCT invoice_id) FROM sales_invoice_line_items WHERE COALESCE(total_amount,0) > 0").fetchone()
print("Sales invoice line items with amounts:", r3[0])
