import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
cols = [r[1] for r in c.execute("PRAGMA table_info(vendors)").fetchall()]
print("vendors:", ", ".join(cols))
cols = [r[1] for r in c.execute("PRAGMA table_info(chart_accounts)").fetchall()]
print("chart_accounts:", ", ".join(cols))
cols = [r[1] for r in c.execute("PRAGMA table_info(sales_invoices)").fetchall()]
print("sales_invoices:", ", ".join(cols))
