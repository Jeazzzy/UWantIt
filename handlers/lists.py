import aiosqlite
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import nav_keyboard
from utils import escape_md
from config import DB_NAME

router = Router()


async def show_list(message: types.Message, status: str, state: FSMContext):
    """Показ списка покупок по статусу"""
    await state.update_data(last_list_status=status)
    titles = {
        "pending": "📋 Ждут решения",
        "buy": "✅ Мои покупки",
        "wait": "⏳ Отложенные",
        "reject": "❌ Отказ"
    }

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT id, name, price, store FROM purchases WHERE user_id=? AND status=? ORDER BY id DESC LIMIT 8',
            (message.from_user.id, status)
        )
        rows = await cursor.fetchall()

    if not rows:
        await message.answer(f"{titles[status]}: *Пусто*", reply_markup=nav_keyboard(), parse_mode="Markdown")
        return

    text = f"{titles[status]}:\n\n"
    for row in rows:
        name = escape_md(row[1])
        price = f"{row[2]:,.0f}₽"
        store = escape_md(row[3])
        text += f"• {name} — {price} ({store})\n"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=f"Открыть {row[1]}", callback_data=f"open_{row[0]}")] for row in
                            rows
                        ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_list")]]
    )

    await message.answer(text, reply_markup=inline_kb, parse_mode="Markdown")


@router.callback_query(F.data == "back_to_list")
async def back_to_list_callback(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к списку покупок"""
    data = await state.get_data()
    last_status = data.get("last_list_status", "pending")
    await show_list(callback.message, last_status, state)
    await callback.answer()
