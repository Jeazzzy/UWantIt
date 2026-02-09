import os
import aiosqlite
from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards import main_inline_keyboard, main_keyboard
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

    await message.answer(
        "💡 Кнопка для быстрого доступа:",
        reply_markup=main_keyboard()
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


@router.message(F.text == "🏠 Главное меню")
async def main_menu_button(message: types.Message, state: FSMContext):
    """Обработка кнопки Главное меню"""
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

    await callback.message.edit_text(
        "📝 **Добавление покупки**\n\n"
        "Шаг 1/6: Введи **название вещи**",
        reply_markup=fsm_nav_inline(),
        parse_mode="Markdown"
    )

    await state.update_data(form_message_id=callback.message.message_id)
    await state.set_state(AddPurchase.waiting_name)
    await callback.answer()


@router.callback_query(F.data == "pending_purchases")
async def pending_purchases_callback(callback: types.CallbackQuery):
    """Покупки, ожидающие решения"""
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "pending" AND reminded = 1 ORDER BY created_at DESC',
            (user_id,)
        )
        purchases = await cursor.fetchall()

    if not purchases:
        text = "⏳ **Ждут решения**\n\nНет покупок, ожидающих решения."
    else:
        text = "⏳ **Ждут решения**\n\n"
        for p in purchases:
            text += f"• **{p[1]}** — {p[2]:,.0f}₽ ({p[3]})\n"

    await callback.message.edit_text(
        text,
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
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
    else:
        text = "✅ **Куплено**\n\n"
        for p in purchases:
            text += f"• **{p[1]}** — {p[2]:,.0f}₽ ({p[3]})\n"

    await callback.message.edit_text(
        text,
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
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
    else:
        text = "❌ **Отменено**\n\n"
        for p in purchases:
            text += f"• **{p[1]}** — {p[2]:,.0f}₽ ({p[3]})\n"

    await callback.message.edit_text(
        text,
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def stats_callback(callback: types.CallbackQuery):
    """Статистика"""
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        # Общая сумма купленного
        cursor = await db.execute(
            'SELECT SUM(price) FROM purchases WHERE user_id = ? AND status = "bought"',
            (user_id,)
        )
        total_bought = (await cursor.fetchone())[0] or 0

        # Общая сумма отмененного
        cursor = await db.execute(
            'SELECT SUM(price) FROM purchases WHERE user_id = ? AND status = "cancelled"',
            (user_id,)
        )
        total_cancelled = (await cursor.fetchone())[0] or 0

        # Количество покупок
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

    await callback.message.edit_text(
        text,
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    """Обработчик команды /start - отправляет главное меню"""
    await state.clear()
    await message.answer(
        "🛒 **Бот импульсивных покупок**\n\n"
        "Помогаю контролировать импульсивные покупки!\n"
        "Выбери действие:",
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню через inline кнопку"""
    await state.clear()
    await callback.message.edit_text(
        "🛒 **Бот импульсивных покупок**\n\n"
        "Помогаю контролировать импульсивные покупки!\n"
        "Выбери действие:",
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "add_purchase")
async def add_purchase_callback(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления покупки"""
    from states import AddPurchase
    from keyboards import fsm_nav_inline

    # ✅ Редактируем ТЕКУЩЕЕ сообщение и сохраняем его ID
    await callback.message.edit_text(
        "📝 **Добавление покупки**\n\n"
        "Шаг 1/6: Введи **название вещи**",
        reply_markup=fsm_nav_inline(),
        parse_mode="Markdown"
    )

    # ✅ Сохраняем ID сообщения формы
    await state.update_data(form_message_id=callback.message.message_id)
    await state.set_state(AddPurchase.waiting_name)
    await callback.answer()


@router.callback_query(F.data == "my_purchases")
async def my_purchases_callback(callback: types.CallbackQuery):
    """Мои покупки"""
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        # Ждут решения
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "pending" AND reminded = 1 ORDER BY created_at DESC',
            (user_id,)
        )
        pending = await cursor.fetchall()

        # Куплено
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "bought" ORDER BY created_at DESC LIMIT 5',
            (user_id,)
        )
        bought = await cursor.fetchall()

        # Отменено
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id = ? AND status = "cancelled" ORDER BY created_at DESC LIMIT 5',
            (user_id,)
        )
        cancelled = await cursor.fetchall()

    text = "📦 **Мои покупки**\n\n"

    if pending:
        text += "⏳ **Ждут решения:**\n"
        for p in pending:
            text += f"• {p[1]} — {p[2]:,.0f}₽ ({p[3]})\n"
        text += "\n"

    if bought:
        text += "✅ **Куплено:**\n"
        for p in bought:
            text += f"• {p[1]} — {p[2]:,.0f}₽\n"
        text += "\n"

    if cancelled:
        text += "❌ **Отменено:**\n"
        for p in cancelled:
            text += f"• {p[1]} — {p[2]:,.0f}₽\n"

    if not pending and not bought and not cancelled:
        text += "У тебя пока нет покупок."

    await callback.message.edit_text(
        text,
        reply_markup=main_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

