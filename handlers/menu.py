from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from keyboards import nav_keyboard, main_inline_keyboard
from states import AddPurchase

router = Router()


@router.message(F.text.in_({"🏠 Главное меню", "🔙 Главное меню"}))
async def go_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню через текст (для FSM форм)"""
    await state.clear()
    await message.answer(
        "🛒 **Бот импульсивных покупок**\n\n"
        "Помогаю контролировать импульсивные покупки!\n"
        "Выбери действие:",
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )


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
        await message.answer(
            "🛒 **Бот импульсивных покупок**\n\n"
            "Помогаю контролировать импульсивные покупки!\n"
            "Выбери действие:",
            reply_markup=main_inline_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "fsm_back")
async def fsm_back_callback(callback: types.CallbackQuery, state: FSMContext):
    """Inline кнопка Назад в FSM"""
    current_state = await state.get_state()
    data = await state.get_data()
    from keyboards import fsm_nav_inline, fsm_time_inline
    from states import AddPurchase

    if current_state == AddPurchase.waiting_price:
        await callback.message.edit_text(
            "📝 **Добавление покупки**\n\n"
            "Шаг 1/6: Введи **название вещи**",
            reply_markup=fsm_nav_inline(),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_name)
    elif current_state == AddPurchase.waiting_store:
        await callback.message.edit_text(
            f"📝 **Добавление покупки**\n\n"
            f"✅ Название: `{data.get('name', 'не указано')}`\n\n"
            f"Шаг 2/6: Введи **цену вещи** (₽)\n\n"
            f"💡 Примеры: `1500`, `1 000 000`",
            reply_markup=fsm_nav_inline(),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_price)
    elif current_state == AddPurchase.waiting_link_desc:
        await callback.message.edit_text(
            f"📝 **Добавление покупки**\n\n"
            f"✅ Название: `{data.get('name')}`\n"
            f"✅ Цена: `{data.get('price', 0):,.0f}₽`\n\n"
            f"Шаг 3/6: Введи **название магазина**",
            reply_markup=fsm_nav_inline(),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_store)
    elif current_state == AddPurchase.waiting_photo:
        await callback.message.edit_text(
            f"📝 **Добавление покупки**\n\n"
            f"✅ Название: `{data.get('name')}`\n"
            f"✅ Цена: `{data.get('price', 0):,.0f}₽`\n"
            f"✅ Магазин: `{data.get('store')}`\n\n"
            f"Шаг 4/6: Введи **ссылку или описание**",
            reply_markup=fsm_nav_inline(show_skip=True),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_link_desc)
    elif current_state == AddPurchase.waiting_delay:
        desc = data.get('link_desc_text', 'пропущено')
        await callback.message.edit_text(
            f"📝 **Добавление покупки**\n\n"
            f"✅ Название: `{data.get('name')}`\n"
            f"✅ Цена: `{data.get('price', 0):,.0f}₽`\n"
            f"✅ Магазин: `{data.get('store')}`\n"
            f"✅ Описание: `{desc[:30] if desc != 'пропущено' else desc}`\n\n"
            f"Шаг 5/6: Отправь **фото вещи**",
            reply_markup=fsm_nav_inline(show_skip=True),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_photo)
    else:
        await callback.message.edit_text(
            "🛒 **Бот импульсивных покупок**\n\n"
            "Помогаю контролировать импульсивные покупки!\n"
            "Выбери действие:",
            reply_markup=main_inline_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "fsm_skip")
async def fsm_skip_callback(callback: types.CallbackQuery, state: FSMContext):
    """Inline кнопка Пропустить"""
    current_state = await state.get_state()
    data = await state.get_data()
    from keyboards import fsm_nav_inline, fsm_time_inline
    from states import AddPurchase

    if current_state == AddPurchase.waiting_link_desc:
        await state.update_data(link_desc_text=None)
        await callback.message.edit_text(
            f"📝 **Добавление покупки**\n\n"
            f"✅ Название: `{data['name']}`\n"
            f"✅ Цена: `{data['price']:,.0f}₽`\n"
            f"✅ Магазин: `{data['store']}`\n"
            f"✅ Описание: пропущено\n\n"
            f"Шаг 5/6: Отправь **фото вещи**",
            reply_markup=fsm_nav_inline(show_skip=True),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_photo)
    elif current_state == AddPurchase.waiting_photo:
        await state.update_data(photo_path=None)
        desc = data.get('link_desc_text', 'пропущено')
        await callback.message.edit_text(
            f"📝 **Добавление покупки**\n\n"
            f"✅ Название: `{data['name']}`\n"
            f"✅ Цена: `{data['price']:,.0f}₽`\n"
            f"✅ Магазин: `{data['store']}`\n"
            f"✅ Фото: пропущено\n\n"
            f"Шаг 6/6: Выбери **задержку до напоминания**",
            reply_markup=fsm_time_inline(),
            parse_mode="Markdown"
        )
        await state.set_state(AddPurchase.waiting_delay)

    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def time_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени через inline кнопку"""
    minutes = int(callback.data.split("_")[1])

    data = await state.get_data()
    from datetime import datetime, timedelta
    remind_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    from config import DB_NAME
    import aiosqlite

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
                         INSERT INTO purchases (user_id, name, price, store, link, description, photo_path, remind_at,
                                                created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (callback.from_user.id, data['name'], data['price'], data['store'],
                               data.get('link_desc_text'), data.get('link_desc_text'),
                               data.get('photo_path'), remind_at, datetime.now().isoformat()))
        await db.commit()

    await callback.message.edit_text(
        f"✅ **Покупка добавлена!**\n\n"
        f"📦 {data['name']}\n"
        f"💰 {data['price']:,.0f}₽\n"
        f"🏪 {data['store']}\n\n"
        f"⏰ Напомню через {minutes} мин!",
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer("✅ Добавлено!")


