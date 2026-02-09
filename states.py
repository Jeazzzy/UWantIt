from aiogram.fsm.state import State, StatesGroup

class AddPurchase(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_store = State()
    waiting_link_desc = State()
    waiting_photo = State()
    waiting_delay = State()

class WaitAgain(StatesGroup):
    waiting_time = State()
