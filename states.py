from aiogram.fsm.state import State, StatesGroup


class AddTaskStates(StatesGroup):
    """Состояния для добавления задачи"""

    waiting_for_text = State()
    waiting_for_time = State()
    waiting_for_category = State()


class DeleteTaskStates(StatesGroup):
    """Состояния для удаления задачи"""

    waiting_for_task_id = State()
