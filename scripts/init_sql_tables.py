from app.database import init_db, sync_engine
from sqlalchemy import text

init_db()
with sync_engine.connect() as conn:
    result = conn.execute(
        text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    )
    tables = [row[0] for row in result]
print(f"Tables created: {len(tables)}")
for t in sorted(tables):
    print(f"  - {t}")
