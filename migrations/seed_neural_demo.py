"""Seed synthetic neural feature data for a live demo - no production data needed.
"""
import os, random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL",
    "mssql+pyodbc://sa:IHE_ERP_2024!@sqlserver/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
Session = sessionmaker(bind=engine)
session = Session()

session.execute(text("DELETE FROM dbo.NeuralFeatureStore"))
session.commit()

now = datetime.now()
total = 0

INSERT_SQL = text("""
    INSERT INTO dbo.NeuralFeatureStore
        (feature_group, entity_id, feature_name, feature_value, feature_json, computed_at)
    VALUES (:fg, :eid, :fn, :fv, :fj, :ca)
""")

for bank in ["BNK-CIB-001", "BNK-HSBC-002", "BNK-QNB-003"]:
    for day in range(90):
        d = now - timedelta(days=day)
        deposit = round(random.uniform(10000, 500000), 2)
        withdrawal = round(random.uniform(5000, 300000), 2)
        net = deposit - withdrawal
        session.execute(INSERT_SQL, {
            "fg": "account",
            "eid": str(hash(bank) % 1000000),
            "fn": "cashflow_daily",
            "fv": net,
            "fj": str({"bank": bank, "date": str(d.date()),
                       "deposit": deposit, "withdrawal": withdrawal}),
            "ca": now,
        })
        total += 1

print(f"  [OK] CashFlow: 3 accounts x 90 days = 270 features")

for i in range(1, 21):
    revenue = round(random.uniform(50000, 2000000), 2)
    inv_count = random.randint(1, 50)
    last_date = (now - timedelta(days=random.randint(1, 60))).date()
    session.execute(INSERT_SQL, {
        "fg": "client",
        "eid": str(hash(f"CLI-{i:04d}") % 1000000),
        "fn": "client_engagement",
        "fv": revenue,
        "fj": str({"client_code": f"CLI-{i:04d}", "invoice_count": inv_count,
                   "last_invoice_date": str(last_date)}),
        "ca": now,
    })
    total += 1

print(f"  [OK] Engagement: 20 client features")

for i in range(1, 31):
    budget = round(random.uniform(100000, 5000000), 2)
    actual = round(budget * random.uniform(0.7, 1.4), 2)
    overrun = round((actual - budget) / budget * 100, 2)
    session.execute(INSERT_SQL, {
        "fg": "pnr",
        "eid": str(hash(f"PNR-{2024000+i}") % 1000000),
        "fn": "pnr_budget_actual",
        "fv": overrun,
        "fj": str({"pnr": f"PNR-{2024000+i}", "budget": budget,
                   "actual": actual, "overrun_pct": overrun}),
        "ca": now,
    })
    total += 1

print(f"  [OK] Overrun: 30 PNR features")

for i in range(50):
    score = round(random.uniform(-2, 3), 4)
    session.execute(INSERT_SQL, {
        "fg": "system",
        "eid": str(hash(f"anomaly-{i}") % 1000000),
        "fn": "anomaly_score",
        "fv": score,
        "fj": str({"event": f"EVT-{i:04d}", "score": score,
                   "flagged": score > 2.0}),
        "ca": now,
    })
    total += 1

session.commit()
session.close()

print(f"\n{'='*60}")
print(f"TOTAL Features inserted: {total}")
print(f"Finished: {datetime.now().isoformat()}")
print(f"{'='*60}")
