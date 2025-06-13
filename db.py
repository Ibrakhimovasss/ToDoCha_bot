import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    description = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)
    deadline = Column(DateTime, nullable=True)

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
