import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import os

from database import create_tables

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

create_tables()


@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! я бот-напоминалка. Чтобы добавить задачу, напиши /add_task"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
