from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from keyboards import main_keyboard, nav_keyboard
from states import AddPurchase

router = Router()


@router.message(F.text.in_({"🏠 Главное меню", "🔙 Главное меню"}))
async def go_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=main_keyboard())


@router.message(F.text.in_(["🛒 Добавить покупку", "📋 Ждут решения", "✅ Мои покупки", "⏳ Отложенные", "❌ Отказ"]))
async def main_menu_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопок главного меню"""
    if message.text == "🛒 Добавить покупку":
        await message.answer("Название вещи?", reply_markup=nav_keyboard())
        await state.set_state(AddPurchase.waiting_name)
    else:
        # Импортируем здесь, чтобы избежать циклических импортов
        from handlers.lists import show_list

        status_map = {
            "📋 Ждут решения": "pending",
            "✅ Мои покупки": "buy",
            "⏳ Отложенные": "wait",
            "❌ Отказ": "reject"
        }
        status = status_map[message.text]
        await show_list(message, status, state)


@router.message(F.text == "🔙 Назад")
async def go_back_step(message: types.Message, state: FSMContext):
    """Обработчик кнопки Назад - возврат на предыдущий шаг FSM"""
    from keyboards import skip_keyboard, photo_keyboard

    current_state = await state.get_state()

    if current_state is None or current_state == AddPurchase.waiting_name:
        await go_main_menu(message, state)
    elif current_state == AddPurchase.waiting_price:
        await message.answer("Название вещи?", reply_markup=nav_keyboard())
        await state.set_state(AddPurchase.waiting_name)
    elif current_state == AddPurchase.waiting_store:
        await message.answer("💰 Цена вещи:", reply_markup=nav_keyboard())
        await state.set_state(AddPurchase.waiting_price)
    elif current_state == AddPurchase.waiting_link_desc:
        await message.answer("🏪 Магазин?", reply_markup=nav_keyboard())
        await state.set_state(AddPurchase.waiting_store)
    elif current_state == AddPurchase.waiting_photo:
        await message.answer("🔗 Ссылка или описание?", reply_markup=skip_keyboard())
        await state.set_state(AddPurchase.waiting_link_desc)
    elif current_state == AddPurchase.waiting_delay:
        await message.answer("📷 Фото вещи? (отправь фото или пропусти)", reply_markup=photo_keyboard())
        await state.set_state(AddPurchase.waiting_photo)
    else:
        await state.clear()
        await message.answer("🏠 Главное меню:", reply_markup=main_keyboard())
