import sqlite3
from typing import List, Tuple, Optional


class Database:
    def _init_(self, db_name: str):
        self.db_name = db_name

    def _get_connection(self):
        """Получение соединения с базой данных."""
        return sqlite3.connect(self.db_name)

    def add_task(
        self,
        user_id: int,
        text: str,
        reminder_time: str,
        category_id: Optional[int] = None,
    ) -> int:
        """Добавление новой задачи в базу данных."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (user_id, category_id, text, reminder_time, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (user_id, category_id, text, reminder_time),
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def add_category(self, user_id: int, name: str) -> int:
        """Добавление новой категории в базу данных."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM categories WHERE user_id = ? AND name = ?", (user_id, name)
        )
        exiting = cursor.fetchone()
        if exiting:
            conn.close()
            return exiting[0]

        cursor.execute(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)", (user_id, name)
        )
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return category_id


def get_user_categories(self, user_id: int) -> List[Tuple[int, str]]:
    """Получение категорий пользователя."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM categories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall()
    conn.close()
    return categories


def get_active_tasks(self) -> List[Tuple]:
    """Получение активных задач пользователя."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT t.id, t.user_id, t.text, t.reminder_time, c.name 
        FROM tasks t 
        LEFT JOIN categories c ON t.category_id = c.id 
        WHERE t.is_active = 1
        ORDER BY t.reminder_time
        """
    )

    tasks = cursor.fetchall()
    conn.close()
    return tasks


def get_user_tasks(self, user_id: int) -> List[Tuple]:
    """Получение задач пользователя."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT t.id, t.text, t.reminder_time,c.name 
        FROM tasks t 
        LEFT JOIN categories c ON t.category_id = c.id 
        WHERE t.user_id = ? AND t.is_active = 1
        ORDER BY t.reminder_time
        """,
        (user_id,),
    )

    tasks = cursor.fetchall()
    conn.close()
    return tasks


def deactivate_task(self, task_id: int) -> bool:
    """Деактивация задачи после напоминания."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE tasks SET is_active = 0 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return True


def delete_task(self, task_id: int) -> bool:
    """Удаление задачи из базы данных."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return True
