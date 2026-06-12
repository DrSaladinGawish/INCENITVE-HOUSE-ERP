import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
try:
    c.execute("ALTER TABLE purchase_invoices ADD COLUMN event_id UUID REFERENCES events(id)")
    c.commit()
    print("Added event_id column to purchase_invoices")
except Exception as e:
    print(f"Error: {e}")
finally:
    c.close()
