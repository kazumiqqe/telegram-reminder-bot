import sqlite3
from datetime import datetime


def create_tables():
    """Создание таблиц в базе данных"""
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()

    # Таблица категорий
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(user_id, name)
    )
    """
    )

    # Таблица задач
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER,
        text TEXT NOT NULL,
        reminder_time TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """
    )

    conn.commit()
    conn.close()
    print("✅ Таблицы созданы!")
    return True
