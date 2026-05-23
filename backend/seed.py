# seed.py
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.seed_data import seed_data

async def main():
    async with AsyncSessionLocal() as db:
        await seed_data(db)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
