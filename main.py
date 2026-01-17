import asyncio, logging, sqlite3, os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()


def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить"), KeyboardButton(text="📋 Список")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
    )


def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            is_sent INTEGER DEFAULT 0
        )
    """
    )
    conn.commit()
    conn.close()


class AddReminder(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()


async def schedule_reminder(user_id: int, text: str, time_str: str, reminder_id: int):
    reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

    async def send_reminder():
        try:
            await bot.send_message(
                user_id, f"🔔 Напоминание!\n\n{text}", reply_markup=main_kb()
            )
            conn = sqlite3.connect("reminders.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,)
            )
            conn.commit()
            conn.close()
        except:
            pass

    scheduler.add_job(
        send_reminder, "date", run_date=reminder_time, id=f"rem_{reminder_id}"
    )


async def load_old_reminders():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, text, reminder_time FROM reminders WHERE is_sent = 0"
    )

    for rid, uid, text, rtime in cursor.fetchall():
        rt = datetime.strptime(rtime, "%Y-%m-%d %H:%M:%S")
        if rt <= datetime.now():
            try:
                await bot.send_message(
                    uid, f"🔔 Напоминание!\n\n{text}", reply_markup=main_kb()
                )
            except:
                pass
            cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (rid,))
        else:
            await schedule_reminder(uid, text, rtime, rid)

    conn.commit()
    conn.close()


def parse_time(t_str: str) -> datetime:
    t_str = t_str.lower().strip()
    now = datetime.now()

    if t_str.startswith("через"):
        parts = t_str.split()
        if len(parts) >= 3:
            num = int(parts[1])
            unit = parts[2]
            if "минут" in unit:
                return now + timedelta(minutes=num)
            if "час" in unit:
                return now + timedelta(hours=num)
            if "день" in unit or "дня" in unit:
                return now + timedelta(days=num)

    if "завтра" in t_str:
        t_part = t_str.replace("завтра", "").replace("в", "").strip()
        if ":" in t_part:
            h, m = map(int, t_part.split(":"))
            return (now + timedelta(days=1)).replace(hour=h, minute=m, second=0)

    if ":" in t_str and len(t_str) <= 5:
        h, m = map(int, t_str.split(":"))
        rt = now.replace(hour=h, minute=m, second=0)
        return rt if rt > now else rt + timedelta(days=1)

    if t_str == "через минуту":
        return now + timedelta(minutes=1)

    raise ValueError("Неверный формат")


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🤖 Бот-напоминалка\nВыберите действие:", reply_markup=main_kb()
    )


@dp.message(lambda m: m.text in ["❓ Помощь", "/help"])
async def help_cmd(message: types.Message):
    await message.answer(
        "📌 Используйте кнопки:\n➕ Добавить - новое напоминание\n📋 Список - ваши напоминания",
        reply_markup=main_kb(),
    )


@dp.message(lambda m: m.text in ["📋 Список", "/list"])
async def list_cmd(message: types.Message):
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT text, reminder_time, is_sent FROM reminders WHERE user_id = ? ORDER BY reminder_time",
        (message.from_user.id,),
    )

    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        await message.answer("📭 Нет напоминаний", reply_markup=main_kb())
        return

    text = "📋 Ваши напоминания:\n\n"
    for i, (task, time_str, sent) in enumerate(tasks, 1):
        status = "✅" if sent else "⏳"
        text += f"{i}. {status} {task}\n   ⏰ {time_str}\n\n"

    await message.answer(text, reply_markup=main_kb())


@dp.message(lambda m: m.text in ["➕ Добавить", "/add"])
async def add_cmd(message: types.Message, state: FSMContext):
    await message.answer("📝 О чем напомнить?", reply_markup=cancel_kb())
    await state.set_state(AddReminder.waiting_for_text)


@dp.message(AddReminder.waiting_for_text)
async def get_text(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await message.answer("❌ Отменено", reply_markup=main_kb())
        await state.clear()
        return

    await state.update_data(text=message.text)
    await message.answer(
        "⏰ Через сколько напомнить?\nПример: через 5 минут, 14:30, завтра в 10:00",
        reply_markup=cancel_kb(),
    )
    await state.set_state(AddReminder.waiting_for_time)


@dp.message(AddReminder.waiting_for_time)
async def get_time(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await message.answer("❌ Отменено", reply_markup=main_kb())
        await state.clear()
        return

    try:
        data = await state.get_data()
        text = data["text"]
        reminder_time = parse_time(message.text)
        time_str = reminder_time.strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, text, reminder_time) VALUES (?, ?, ?)",
            (message.from_user.id, text, time_str),
        )
        rid = cursor.lastrowid
        conn.commit()
        conn.close()

        await schedule_reminder(message.from_user.id, text, time_str, rid)
        await message.answer(
            f"✅ Добавлено!\n📝 {text}\n⏰ {time_str}", reply_markup=main_kb()
        )

    except ValueError as e:
        await message.answer(
            f"❌ Ошибка: {e}\nПопробуйте еще раз", reply_markup=cancel_kb()
        )
        return
    except Exception as e:
        await message.answer("❌ Ошибка, попробуйте снова", reply_markup=main_kb())

    await state.clear()


@dp.message(lambda m: m.text == "❌ Отмена")
async def cancel_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=main_kb())


async def main():
    init_db()
    scheduler.start()
    await load_old_reminders()

    print("🤖 Бот запущен")
    await dp.start_polling(bot)
    scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
