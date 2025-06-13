# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv
from db import init_db, add_task, list_tasks, complete_task

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Assalomu alaykum! To-do botga xush kelibsiz.\n\n"
                         "<b>/add</b> — Vazifa qo‘shish\n"
                         "<b>/list</b> — Vazifalar ro‘yxati\n"
                         "<b>/done</b> — Vazifani bajarilgan deb belgilash (masalan: /done 3)")

@dp.message(Command("add"))
async def add_cmd(message: Message):
    task = message.text[5:].strip()
    if not task:
        await message.answer("Vazifa matnini yozing, masalan:\n<code>/add Kitob o‘qish</code>")
        return
    await add_task(message.from_user.id, task)
    await message.answer("✅ Vazifa qo‘shildi!")

@dp.message(Command("list"))
async def list_cmd(message: Message):
    tasks = await list_tasks(message.from_user.id)
    if not tasks:
        await message.answer("🗒️ Sizda hali vazifalar yo‘q.")
        return

    msg = "<b>📋 Vazifalaringiz:</b>\n"
    for task in tasks:
        status = "✅" if task[2] else "⏳"
        msg += f"{task[0]}. {task[1]} {status}\n"
    await message.answer(msg)

@dp.message(Command("done"))
async def done_cmd(message: Message):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❗ To‘g‘ri yozing: /done <task_id>\nMasalan: /done 2")
        return
    task_id = int(args[1])
    await complete_task(message.from_user.id, task_id)
    await message.answer("✅ Vazifa bajarildi deb belgilandi!")

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
