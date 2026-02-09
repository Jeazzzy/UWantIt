from aiogram.fsm.state import State, StatesGroup

class AddPurchase(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_store = State()
    waiting_link_desc = State()
    waiting_photo = State()
    waiting_delay = State()
    waiting_delete_id = State()
    waiting_move_target = State()
    waiting_delete_confirm = State()

class WaitMore(StatesGroup):
    waiting_new_delay = State()
