from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)