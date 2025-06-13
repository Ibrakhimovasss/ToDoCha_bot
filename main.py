import os
from datetime import datetime
from typing import Optional, AsyncIterator

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import Task, get_db_session, init_db

load_dotenv()

class TaskStates(StatesGroup):
    description = State()
    deadline = State()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

async def get_user_tasks(user_id: int, session: AsyncSession) -> list[Task]:
    result = await session.execute(select(Task).where(Task.user_id == user_id))
    return result.scalars().all()

async def create_task(user_id: int, description: str, deadline: Optional[datetime], session: AsyncSession) -> Task:
    task = Task(user_id=user_id, description=description, deadline=deadline)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

async def mark_task_done(task_id: int, user_id: int, session: AsyncSession) -> bool:
    result = await session.execute(
        update(Task)
        .where(Task.id == task_id, Task.user_id == user_id)
        .values(is_done=True)
    )
    await session.commit()
    return result.rowcount > 0

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = """
    📝 To-Do Bot Help:
    
    /new - Create a new task
    /show - Show your tasks
    /finish <id> - Mark a task as done
    
    Simply send a command to get started!
    """
    await message.answer(welcome_text)

@dp.message(Command("new"))
async def cmd_new(message: Message, state: FSMContext):
    await message.answer("Please enter the task description:")
    await state.set_state(TaskStates.description)

@dp.message(TaskStates.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Please enter the deadline (YYYY-MM-DD) or send /skip:")
    await state.set_state(TaskStates.deadline)

@dp.message(TaskStates.deadline)
async def process_deadline(message: Message, state: FSMContext):
    data = await state.get_data()
    description = data["description"]
    deadline = None
    
    if message.text != "/skip":
        try:
            deadline = datetime.strptime(message.text, "%Y-%m-%d")
        except ValueError:
            await message.answer("Invalid date format. Please use YYYY-MM-DD or /skip")
            return
    
    session_gen = get_db_session()
    session = await anext(session_gen)
    try:
        task = await create_task(message.from_user.id, description, deadline, session)
        
        response = f"✅ Task created!\n\n{description}"
        if deadline:
            response += f"\nDeadline: {deadline.strftime('%Y-%m-%d')}"
        
        await message.answer(response)
    finally:
        await session.close()
    await state.clear()

@dp.message(Command("show"))
async def cmd_show(message: Message):
    session_gen = get_db_session()
    session = await anext(session_gen)
    try:
        tasks = await get_user_tasks(message.from_user.id, session)
        
        if not tasks:
            await message.answer("You don't have any tasks yet. Use /new to create one!")
            return
        
        response = "📋 Your Tasks:\n\n"
        for task in tasks:
            status = "✅" if task.is_done else "⏳"
            deadline_info = f" | Deadline: {task.deadline.strftime('%Y-%m-%d')}" if task.deadline else ""
            response += f"{task.id}. {status} {task.description}{deadline_info}\n"
        
        await message.answer(response)
    finally:
        await session.close()


@dp.message(Command("finish"))
async def cmd_finish(message: Message):
    try:
        task_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Please specify a valid task ID. Example: /finish 1")
        return
    
    session_gen = get_db_session()
    session = await anext(session_gen)
    try:
        success = await mark_task_done(task_id, message.from_user.id, session)
        
        if success:
            await message.answer(f"✅ Task {task_id} marked as done!")
        else:
            await message.answer("Task not found or already completed.")
    finally:
        await session.close()

@dp.startup()
async def on_startup(dispatcher: Dispatcher):
    await init_db()
    print("Bot started and database initialized")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
