# db.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Boolean, select, update

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)

# Init DB: create table if not exists
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Add task
async def add_task(user_id: int, description: str):
    async with async_session() as session:
        task = Task(user_id=user_id, description=description)
        session.add(task)
        await session.commit()

# List tasks
async def list_tasks(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Task).where(Task.user_id == user_id)
        )
        return result.scalars().all()

# Complete task
async def complete_task(user_id: int, task_id: int):
    async with async_session() as session:
        await session.execute(
            update(Task)
            .where(Task.user_id == user_id, Task.id == task_id)
            .values(is_done=True)
        )
        await session.commit()
