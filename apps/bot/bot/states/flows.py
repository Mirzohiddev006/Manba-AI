"""FSM holatlari — Redis da saqlanadi (bot qayta ishga tushsa yo'qolmaydi)."""

from aiogram.fsm.state import State, StatesGroup


class EditSource(StatesGroup):
    choosing_field = State()
    entering_value = State()


class SpellFlow(StatesGroup):
    reviewing = State()


class FeedbackFlow(StatesGroup):
    writing = State()
