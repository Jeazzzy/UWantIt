import os
import aiosqlite
from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from keyboards import main_inline_keyboard
from config import DB_NAME

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Команда /start"""
    await state.clear()

    user_id = message.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.commit()

    await message.answer(
        "🛒 **Бот импульсивных покупок**\n\n"
        "Помогаю контролировать импульсивные покупки!\n"
        "Выбери действие:",
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    """Команда /menu"""
    await state.clear()
    await message.answer(
        "🛒 **Бот импульсивных покупок**\n\n"
        "Помогаю контролировать импульсивные покупки!\n"
        "Выбери действие:",
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_purchase")
async def add_purchase_callback(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления покупки"""
    from states import AddPurchase
    from keyboards import fsm_nav_inline

    try:
        await callback.message.edit_text(
            "📝 **Добавление покупки**\n\n"
            "Шаг 1/6: Введи **название вещи**",
            reply_markup=fsm_nav_inline(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

    await state.update_data(form_message_id=callback.message.message_id)
    await state.set_state(AddPurchase.waiting_name)
    await callback.answer()


@router.callback_query(F.data == "pending_purchases")
async def pending_purchases_callback(callback: types.CallbackQuery):
    """Покупки, ожидающие решения"""
    from datetime import datetime
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store, remind_at FROM purchases WHERE user_id = ? AND status = "pending" AND reminded = 0 ORDER BY remind_at ASC',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "⏳ **Ждут решения**\n\nНет покупок, ожидающих решения."
        keyboard = main_inline_keyboard()
    else:
        text = "⏳ **Ждут решения**\n\n"
        now = datetime.now()

        buttons = []

        for p in purchases:
            purchase_id, name, price, store, remind_at_str = p

            try:
                remind_at = datetime.fromisoformat(remind_at_str)
                time_left = remind_at - now

                if time_left.total_seconds() <= 0:
                    time_str = "⏰"
                else:
                    days = time_left.days
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60

                    if days > 0:
                        time_str = f"⏱️ {days}д {hours}ч"
                    elif hours > 0:
                        time_str = f"⏱️ {hours}ч {minutes}м"
                    else:
                        time_str = f"⏱️ {minutes}м"
            except:
                time_str = "⏱️"

            text += f"{time_str} **{name}** — {price:,.0f}₽\n"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"👁️ {name[:25]}...",
                    callback_data=f"view_{purchase_id}"
                )
            ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


@router.callback_query(F.data == "bought_purchases")
async def bought_purchases_callback(callback: types.CallbackQuery):
    """Купленные покупки"""
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "bought" ORDER BY created_at DESC LIMIT 10',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "✅ **Куплено**\n\nНет купленных покупок."
        keyboard = main_inline_keyboard()
    else:
        text = "✅ **Куплено**\n\n"
        buttons = []

        for p in purchases:
            purchase_id, name, price, store = p
            text += f"• **{name}** — {price:,.0f}₽ ({store})\n"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"👁️ {name[:25]}...",
                    callback_data=f"view_{purchase_id}"
                )
            ])

        # ✅ Добавляем кнопку "Назад"
        buttons.append([
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


@router.callback_query(F.data == "cancelled_purchases")
async def cancelled_purchases_callback(callback: types.CallbackQuery):
    """Отмененные покупки"""
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "cancelled" ORDER BY created_at DESC LIMIT 10',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "❌ **Отменено**\n\nНет отмененных покупок."
        keyboard = main_inline_keyboard()
    else:
        text = "❌ **Отменено**\n\n"
        buttons = []

        for p in purchases:
            purchase_id, name, price, store = p
            text += f"• **{name}** — {price:,.0f}₽ ({store})\n"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"👁️ {name[:25]}...",
                    callback_data=f"view_{purchase_id}"
                )
            ])

        # ✅ Добавляем кнопку "Назад"
        buttons.append([
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


@router.callback_query(F.data == "stats")
async def stats_callback(callback: types.CallbackQuery):
    """Статистика"""
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT SUM(price) FROM purchases WHERE user_id = ? AND status = "bought"',
            (user_id,)
        )
        total_bought = (await cursor.fetchone())[0] or 0

        cursor = await db.execute(
            'SELECT SUM(price) FROM purchases WHERE user_id = ? AND status = "cancelled"',
            (user_id,)
        )
        total_cancelled = (await cursor.fetchone())[0] or 0

        cursor = await db.execute(
            'SELECT COUNT(*) FROM purchases WHERE user_id = ? AND status = "bought"',
            (user_id,)
        )
        count_bought = (await cursor.fetchone())[0]

        cursor = await db.execute(
            'SELECT COUNT(*) FROM purchases WHERE user_id = ? AND status = "cancelled"',
            (user_id,)
        )
        count_cancelled = (await cursor.fetchone())[0]

    text = (
        f"📊 **Статистика**\n\n"
        f"✅ Куплено: {count_bought} шт. на {total_bought:,.0f}₽\n"
        f"❌ Отменено: {count_cancelled} шт. на {total_cancelled:,.0f}₽\n\n"
        f"💰 Сэкономлено: {total_cancelled:,.0f}₽"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=main_inline_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ===== ПРОСМОТР КАРТОЧЕК =====

@router.callback_query(F.data.startswith("view_"))
async def view_purchase_callback(callback: types.CallbackQuery):
    """Просмотр карточки товара"""
    from datetime import datetime
    purchase_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT name, price, store, link, description, photo_path, remind_at, status FROM purchases WHERE id = ? AND user_id = ?',
            (purchase_id, user_id)
        )
        purchase = await cursor.fetchone()

    if not purchase:
        await callback.answer("❌ Покупка не найдена!")
        return

    name, price, store, link, desc, photo_path, remind_at_str, status = purchase

    # Формируем текст карточки
    text = f"🛍️ **{name}**\n\n"
    text += f"💰 **Цена:** {price:,.0f}₽\n"
    text += f"🏪 **Магазин:** {store}\n"

    if desc:
        text += f"\n📝 **Описание:**\n{desc}\n"

    if link:
        text += f"\n🔗 [Открыть ссылку]({link})\n"

    # Время (только для pending)
    if status == "pending":
        try:
            remind_at = datetime.fromisoformat(remind_at_str)
            now = datetime.now()
            time_left = remind_at - now

            if time_left.total_seconds() <= 0:
                time_str = "⏰ Время вышло!"
            else:
                days = time_left.days
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60

                if days > 0:
                    time_str = f"⏱️ Осталось: {days}д {hours}ч {minutes}м"
                elif hours > 0:
                    time_str = f"⏱️ Осталось: {hours}ч {minutes}м"
                else:
                    time_str = f"⏱️ Осталось: {minutes}м"

            text += f"\n{time_str}"
        except:
            pass

    # Статус
    status_emoji = {"pending": "⏳", "bought": "✅", "cancelled": "❌"}
    status_text = {"pending": "Ожидает", "bought": "Куплено", "cancelled": "Отменено"}
    text += f"\n\n{status_emoji.get(status, '❓')} **Статус:** {status_text.get(status, 'Неизвестно')}"

    # Динамическая кнопка "Назад"
    if status == "pending":
        back_button = types.InlineKeyboardButton(text="🔙 К списку", callback_data="back_to_pending")
    elif status == "bought":
        back_button = types.InlineKeyboardButton(text="🔙 К списку", callback_data="back_to_bought")
    else:
        back_button = types.InlineKeyboardButton(text="🔙 К списку", callback_data="back_to_cancelled")

    # Кнопки действий
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="📦 Переместить в...", callback_data=f"move_menu_{purchase_id}"),
            types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_confirm_{purchase_id}")
        ],
        [back_button]
    ])

    # Отправляем карточку
    try:
        if photo_path and os.path.exists(photo_path):
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=types.FSInputFile(photo_path),
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ===== УДАЛЕНИЕ =====

@router.callback_query(F.data.startswith("delete_confirm_"))
async def delete_confirm_callback(callback: types.CallbackQuery):
    """Подтверждение удаления покупки"""
    purchase_id = int(callback.data.split("_")[2])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_yes_{purchase_id}"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_{purchase_id}")
        ]
    ])

    text = (
        "⚠️ **Подтверждение удаления**\n\n"
        "Ты уверен, что хочешь **безвозвратно удалить** эту покупку?\n\n"
        "Это действие **нельзя отменить**!"
    )

    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except TelegramBadRequest:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("delete_yes_"))
async def delete_yes_callback(callback: types.CallbackQuery):
    """Удаление покупки из БД"""
    purchase_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    # Получаем статус ПЕРЕД удалением
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT photo_path, status FROM purchases WHERE id = ? AND user_id = ?',
            (purchase_id, user_id)
        )
        result = await cursor.fetchone()

        if not result:
            await callback.answer("❌ Покупка не найдена!")
            return

        photo_path, status = result

        # Удаляем фото
        if photo_path and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except:
                pass

        # Удаляем из БД
        await db.execute('DELETE FROM purchases WHERE id = ? AND user_id = ?', (purchase_id, user_id))
        await db.commit()

    # ✅ НЕ удаляем сообщение, а редактируем его на список
    from datetime import datetime

    if status == "pending":
        # Список "Ждут решения"
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                'SELECT id, name, price, store, remind_at FROM purchases WHERE user_id = ? AND status = "pending" AND reminded = 0 ORDER BY remind_at ASC',
                (user_id,)
            )
            purchases = await cursor.fetchall()

        if not purchases:
            text = "⏳ **Ждут решения**\n\nНет покупок, ожидающих решения."
            keyboard = main_inline_keyboard()
        else:
            text = "⏳ **Ждут решения**\n\n"
            now = datetime.now()
            buttons = []

            for p in purchases:
                pid, name, price, store, remind_at_str = p

                try:
                    remind_at = datetime.fromisoformat(remind_at_str)
                    time_left = remind_at - now

                    if time_left.total_seconds() <= 0:
                        time_str = "⏰"
                    else:
                        days = time_left.days
                        hours = time_left.seconds // 3600
                        minutes = (time_left.seconds % 3600) // 60

                        if days > 0:
                            time_str = f"⏱️ {days}д {hours}ч"
                        elif hours > 0:
                            time_str = f"⏱️ {hours}ч {minutes}м"
                        else:
                            time_str = f"⏱️ {minutes}м"
                except:
                    time_str = "⏱️"

                text += f"{time_str} **{name}** — {price:,.0f}₽\n"

                buttons.append([
                    types.InlineKeyboardButton(
                        text=f"👁️ {name[:25]}...",
                        callback_data=f"view_{pid}"
                    )
                ])

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    elif status == "bought":
        # Список "Куплено"
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "bought" ORDER BY created_at DESC LIMIT 10',
                (user_id,)
            )
            purchases = await cursor.fetchall()

        if not purchases:
            text = "✅ **Куплено**\n\nНет купленных покупок."
            keyboard = main_inline_keyboard()
        else:
            text = "✅ **Куплено**\n\n"
            buttons = []

            for p in purchases:
                pid, name, price, store = p
                text += f"• **{name}** — {price:,.0f}₽ ({store})\n"

                buttons.append([
                    types.InlineKeyboardButton(
                        text=f"👁️ {name[:25]}...",
                        callback_data=f"view_{pid}"
                    )
                ])

            buttons.append([
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
            ])

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    else:  # cancelled
        # Список "Отменено"
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "cancelled" ORDER BY created_at DESC LIMIT 10',
                (user_id,)
            )
            purchases = await cursor.fetchall()

        if not purchases:
            text = "❌ **Отменено**\n\nНет отмененных покупок."
            keyboard = main_inline_keyboard()
        else:
            text = "❌ **Отменено**\n\n"
            buttons = []

            for p in purchases:
                pid, name, price, store = p
                text += f"• **{name}** — {price:,.0f}₽ ({store})\n"

                buttons.append([
                    types.InlineKeyboardButton(
                        text=f"👁️ {name[:25]}...",
                        callback_data=f"view_{pid}"
                    )
                ])

            buttons.append([
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
            ])

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    # ✅ Редактируем сообщение (если текст) или удаляем и отправляем новое (если фото)
    try:
        if callback.message.photo:
            # Если было фото - удаляем и отправляем список
            await callback.message.delete()
            await callback.message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Если был текст - редактируем
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except TelegramBadRequest:
        pass

    await callback.answer("🗑️ Покупка удалена!")


# ===== ПЕРЕМЕЩЕНИЕ =====

@router.callback_query(F.data.startswith("move_menu_"))
async def move_menu_callback(callback: types.CallbackQuery):
    """Меню выбора статуса для перемещения"""
    purchase_id = int(callback.data.split("_")[2])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="⏳ Ждут решения", callback_data=f"move_pending_{purchase_id}"),
        ],
        [
            types.InlineKeyboardButton(text="✅ Куплено", callback_data=f"move_bought_{purchase_id}"),
            types.InlineKeyboardButton(text="❌ Отменено", callback_data=f"move_cancelled_{purchase_id}")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_{purchase_id}")
        ]
    ])

    text = (
        "📦 **Переместить покупку**\n\n"
        "Выбери новый статус:"
    )

    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except TelegramBadRequest:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("move_pending_"))
async def move_pending_callback(callback: types.CallbackQuery, state: FSMContext):
    """Перемещение в Ждут решения - выбор времени"""
    from states import WaitAgain
    purchase_id = int(callback.data.split("_")[2])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="5 мин", callback_data=f"movetime_{purchase_id}_5"),
            types.InlineKeyboardButton(text="30 мин", callback_data=f"movetime_{purchase_id}_30")
        ],
        [
            types.InlineKeyboardButton(text="1 час", callback_data=f"movetime_{purchase_id}_60"),
            types.InlineKeyboardButton(text="6 часов", callback_data=f"movetime_{purchase_id}_360")
        ],
        [
            types.InlineKeyboardButton(text="1 день", callback_data=f"movetime_{purchase_id}_1440"),
            types.InlineKeyboardButton(text="3 дня", callback_data=f"movetime_{purchase_id}_4320")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"move_menu_{purchase_id}")
        ]
    ])

    text = (
        "⏳ **Переместить в Ждут решения**\n\n"
        "Выбери время напоминания или напиши минуты (например: `15`, `120`)"
    )

    # Сохраняем для текстового ввода
    await state.update_data(
        move_purchase_id=purchase_id,
        move_message_id=callback.message.message_id
    )
    await state.set_state(WaitAgain.waiting_time)

    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except TelegramBadRequest:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("movetime_"))
async def movetime_callback(callback: types.CallbackQuery, state: FSMContext):
    """Перемещение в Ждут решения с выбранным временем"""
    from datetime import datetime, timedelta
    await state.clear()

    parts = callback.data.split("_")
    purchase_id = int(parts[1])
    minutes = int(parts[2])

    new_remind_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE purchases SET status = "pending", remind_at = ?, reminded = 0 WHERE id = ?',
            (new_remind_at, purchase_id)
        )
        await db.commit()

    await callback.message.delete()

    if minutes < 60:
        time_str = f"{minutes} мин"
    elif minutes < 1440:
        time_str = f"{minutes // 60} ч"
    else:
        time_str = f"{minutes // 1440} дн"

    await callback.answer(f"✅ Перемещено! Напомню через {time_str}")


@router.callback_query(F.data.startswith("move_bought_"))
async def move_bought_callback(callback: types.CallbackQuery):
    """Перемещение в Куплено"""
    purchase_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status = "bought" WHERE id = ?', (purchase_id,))
        await db.commit()

    await callback.message.delete()
    await callback.answer("✅ Перемещено в Куплено!")


@router.callback_query(F.data.startswith("move_cancelled_"))
async def move_cancelled_callback(callback: types.CallbackQuery):
    """Перемещение в Отменено"""
    purchase_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status = "cancelled" WHERE id = ?', (purchase_id,))
        await db.commit()

    await callback.message.delete()
    await callback.answer("❌ Перемещено в Отменено!")


# ===== ВОЗВРАТ К СПИСКАМ =====

@router.callback_query(F.data == "back_to_pending")
async def back_to_pending_callback(callback: types.CallbackQuery):
    """Возврат к списку ожидающих покупок"""
    await callback.message.delete()

    from datetime import datetime
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store, remind_at FROM purchases WHERE user_id = ? AND status = "pending" AND reminded = 0 ORDER BY remind_at ASC',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "⏳ **Ждут решения**\n\nНет покупок, ожидающих решения."
        keyboard = main_inline_keyboard()
    else:
        text = "⏳ **Ждут решения**\n\n"
        now = datetime.now()

        buttons = []

        for p in purchases:
            purchase_id, name, price, store, remind_at_str = p

            try:
                remind_at = datetime.fromisoformat(remind_at_str)
                time_left = remind_at - now

                if time_left.total_seconds() <= 0:
                    time_str = "⏰"
                else:
                    days = time_left.days
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60

                    if days > 0:
                        time_str = f"⏱️ {days}д {hours}ч"
                    elif hours > 0:
                        time_str = f"⏱️ {hours}ч {minutes}м"
                    else:
                        time_str = f"⏱️ {minutes}м"
            except:
                time_str = "⏱️"

            text += f"{time_str} **{name}** — {price:,.0f}₽\n"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"👁️ {name[:25]}...",
                    callback_data=f"view_{purchase_id}"
                )
            ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_bought")
async def back_to_bought_callback(callback: types.CallbackQuery):
    """Возврат к списку купленных покупок"""
    await callback.message.delete()

    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "bought" ORDER BY created_at DESC LIMIT 10',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "✅ **Куплено**\n\nНет купленных покупок."
        keyboard = main_inline_keyboard()
    else:
        text = "✅ **Куплено**\n\n"
        buttons = []

        for p in purchases:
            purchase_id, name, price, store = p
            text += f"• **{name}** — {price:,.0f}₽ ({store})\n"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"👁️ {name[:25]}...",
                    callback_data=f"view_{purchase_id}"
                )
            ])

        # ✅ Добавляем кнопку "Назад"
        buttons.append([
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_cancelled")
async def back_to_cancelled_callback(callback: types.CallbackQuery):
    """Возврат к списку отмененных покупок"""
    await callback.message.delete()

    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "cancelled" ORDER BY created_at DESC LIMIT 10',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "❌ **Отменено**\n\nНет отмененных покупок."
        keyboard = main_inline_keyboard()
    else:
        text = "❌ **Отменено**\n\n"
        buttons = []

        for p in purchases:
            purchase_id, name, price, store = p
            text += f"• **{name}** — {price:,.0f}₽ ({store})\n"

            buttons.append([
                types.InlineKeyboardButton(
                    text=f"👁️ {name[:25]}...",
                    callback_data=f"view_{purchase_id}"
                )
            ])

        # ✅ Добавляем кнопку "Назад"
        buttons.append([
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    try:
        await callback.message.edit_text(
            "🛒 **Бот импульсивных покупок**\n\n"
            "Помогаю контролировать импульсивные покупки!\n"
            "Выбери действие:",
            reply_markup=main_inline_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        pass

    await callback.answer()
