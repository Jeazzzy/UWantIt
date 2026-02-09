import aiosqlite
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import escape_md
from config import DB_NAME

router = Router()

# Обработчики inline-кнопок для открытия списков
@router.callback_query(F.data.startswith("list_"))
async def list_callback(callback: types.CallbackQuery, state: FSMContext):
    """Открытие списка по статусу через inline кнопку"""
    status = callback.data.split("_")[1]
    await show_list(callback.message, status, state, is_callback=True)
    await callback.answer()

async def show_list(message: types.Message, status: str, state: FSMContext, is_callback: bool = False):
    """Показ списка покупок по статусу"""
    await state.update_data(last_list_status=status)
    titles = {
        "pending": "📋 Ждут решения",
        "buy": "✅ Куплено",
        "wait": "⏳ Отложено",
        "reject": "❌ Отказы"
    }

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id=? AND status=? ORDER BY id DESC LIMIT 8',
            (message.from_user.id, status)
        )
        rows = await cursor.fetchall()

    if not rows:
        text = f"{titles[status]}\n\n📭 **Пусто**"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
            ]
        )
    else:
        text = f"{titles[status]}:\n\n"
        for row in rows:
            name = escape_md(row[1])
            price = f"{row[2]:,.0f}₽"
            store = escape_md(row[3])
            text += f"• {name} — {price} ({store})\n"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"📦 {row[1][:20]}...", callback_data=f"open_{row[0]}")]
                for row in rows
            ] + [[InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]]
        )

    # Если вызвано через callback - редактируем, иначе - новое сообщение
    if is_callback:
        await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "back_to_list")
async def back_to_list_callback(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к списку покупок"""
    data = await state.get_data()
    last_status = data.get("last_list_status", "pending")
    await show_list(callback.message, last_status, state, is_callback=True)
    await callback.answer()
