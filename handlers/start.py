from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_keyboard

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer("🛒 Бот импульсивных покупок!", reply_markup=main_keyboard())
