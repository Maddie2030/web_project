from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

DATABASE_URL = "postgresql+asyncpg://postgresuser:postgresspassword@localhost:5432/auth_db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# REQUIRED FIX:
@asynccontextmanager
async def get_session():
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

# Optional: database init and shutdown handlers
async def init_db():
    async with engine.begin() as conn:
        # You can run migrations or check DB connection here
        await conn.run_sync(lambda _: None)

async def close_db():
    await engine.dispose()
