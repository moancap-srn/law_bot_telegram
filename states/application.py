from aiogram.fsm.state import State, StatesGroup


class ApplicationForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_question = State()
    waiting_for_time = State()
