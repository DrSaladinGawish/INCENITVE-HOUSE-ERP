import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")

tables = ["sales_invoices", "purchase_invoices", "bank_transactions", "payment_vouchers", "receipt_vouchers", "journal_vouchers", "job_line_items", "sales_invoice_line_items", "quotation_line_items"]
for t in tables:
    cur = c.execute("PRAGMA table_info({})".format(t))
    cols = [row[1] for row in cur.fetchall()]
    print(f"{t:35} {', '.join(cols)}")
