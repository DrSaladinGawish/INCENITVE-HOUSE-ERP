import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
checks = [
    ("bank_transactions", "amount"),
    ("purchase_invoices", "total_amount"),
    ("payment_vouchers", "amount"),
    ("sales_invoices", "total_amount"),
    ("journal_vouchers", "amount"),
    ("receipt_vouchers", "amount"),
]
total = 0
with_amt = 0
for t, col in checks:
    cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    amt = c.execute(f"SELECT COUNT(*) FROM {t} WHERE {col} IS NOT NULL AND {col} != 0").fetchone()[0]
    pct = round(amt/cnt*100, 1) if cnt else 0
    total += cnt
    with_amt += amt
    print(f"{t:30} {amt:>5}/{cnt} ({pct:>5.1f}%)")
density = round(with_amt/total*100, 1) if total else 0
print(f"\nOverall: {with_amt}/{total} ({density}%)")
