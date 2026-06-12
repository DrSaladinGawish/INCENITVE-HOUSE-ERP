"""Minimal demo data seeder — creates admin user + sample data."""
import asyncio
from app.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.scripts.seed_test_data import seed_all, verify_gates


async def create_admin():
    async with SessionLocal() as db:
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == "admin@eventcore.com"))
        if not existing.scalar_one_or_none():
            db.add(User(
                email="admin@eventcore.com",
                full_name="Admin User",
                role="admin",
                password_hash=hash_password("admin123"),
                is_active=True,
            ))
            await db.commit()
            print("Admin user created (admin@eventcore.com / admin123)")
        else:
            print("Admin user already exists")


async def seed():
    await create_admin()
    async with SessionLocal() as db:
        result = await seed_all(db)
        print(f"Seed: {result.get('status')}")
        if result.get("status") == "seeded":
            for k, v in result.items():
                if k != "status":
                    print(f"  {k}: {v}")
        gates = await verify_gates(db)
        passed = sum(1 for v in gates.values() if isinstance(v, dict) and v.get("pass"))
        print(f"\nGates passed: {passed}/{gates.get('total_gates', 6)}")


if __name__ == "__main__":
    asyncio.run(seed())
