import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
try:
    c.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
    c.commit()
    print("Added password_hash column")
except Exception as e:
    print(f"Column may already exist: {e}")
finally:
    c.close()
