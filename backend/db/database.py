from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import dotenv
import os

if not dotenv.load_dotenv():
    raise RuntimeError("Не удалось загрузить файл окружения")

DATABASE_URL= os.getenv("DATABASE_URL")

DATABASE_URL = f"postgresql+asyncpg://{DATABASE_URL}"

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

__all__ = ["Base", "get_db"]

from db.models import *