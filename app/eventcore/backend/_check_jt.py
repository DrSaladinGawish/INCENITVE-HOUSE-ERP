import sqlite3
c = sqlite3.connect("D:\\EventCore_ERP\\backend\\eventcore.db")
r = c.execute("SELECT source_type, COUNT(*) FROM job_line_items WHERE source_type IS NOT NULL GROUP BY source_type").fetchall()
print("Source types:", r)
r2 = c.execute("SELECT COUNT(*) FROM job_line_items WHERE source_type IS NULL").fetchone()
print("NULL source_type:", r2[0])
r3 = c.execute("SELECT COUNT(*) FROM job_line_items").fetchone()
print("Total job_line_items:", r3[0])
