import os
import aiosqlite
from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from keyboards import main_keyboard
from utils import escape_md
from states import AddPurchase
from config import DB_NAME

router = Router()


@router.callback_query(F.data.startswith("open_"))
async def open_purchase_callback(callback: types.CallbackQuery, state: FSMContext):
    """Открытие карточки покупки"""
    purchase_id = int(callback.data.split("_")[1])
    await state.update_data(last_viewed_id=purchase_id)

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT name, price, store, link, description, photo_path FROM purchases WHERE id=? AND user_id=?',
            (purchase_id, callback.from_user.id)
        )
        row = await cursor.fetchone()

    if not row:
        await callback.message.answer("❌ Товар не найден!", reply_markup=main_keyboard())
        return

    text = f"📦 *{escape_md(row[0])}*\n💰 {row[1]:,.0f}₽\n🏪 {escape_md(row[2])}"
    if row[4]:
        text += f"\n\n{escape_md(row[4])}"
    if row[3]:
        text += f"\n🔗 {escape_md(row[3])}"

    action_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗑️ Удалить"), KeyboardButton(text="🔄 Переместить")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

    if row[5] and os.path.exists(row[5]):
        await callback.bot.send_photo(
            callback.from_user.id,
            FSInputFile(row[5]),
            caption=text,
            reply_markup=action_kb,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(text, reply_markup=action_kb, parse_mode="Markdown")

    await callback.answer()


@router.message(F.text.in_(["🗑️ Удалить", "🔄 Переместить", "🔙 Назад", "🏠 Главное меню"]))
async def handle_card_actions(message: types.Message, state: FSMContext):
    """Обработка действий с карточкой"""
    from handlers.menu import go_main_menu
    from handlers.lists import show_list

    data = await state.get_data()
    purchase_id = data.get('last_viewed_id')

    if message.text == "🗑️ Удалить":
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute('SELECT name FROM purchases WHERE id=? AND user_id=?',
                                      (purchase_id, message.from_user.id))
            row = await cursor.fetchone()
            if row:
                name = row[0]
                confirm_kb = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text=f"🗑️ УДАЛИТЬ '{name[:30]}...'")],
                        [KeyboardButton(text="❌ Отмена"), KeyboardButton(text="🏠 Главное меню")]
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                await state.update_data(pending_delete_id=purchase_id, pending_delete_name=name)
                await message.answer(
                    f"🗑️ **Подтверди удаление**:\n\n"
                    f"**{escape_md(name)}**\n\n"
                    f"Уверен, что хочешь **НАВСЕГДА** удалить эту покупку?",
                    reply_markup=confirm_kb,
                    parse_mode="Markdown"
                )
                await state.set_state(AddPurchase.waiting_delete_confirm)
                return

    elif message.text == "🔄 Переместить":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                ["📋 Ждут решения", "✅ Мои покупки"],
                ["⏳ Отложенные", "❌ Отказ"],
                ["🔙 Назад", "🏠 Главное меню"]
            ],
            resize_keyboard=True
        )
        await message.answer("📂 **Куда переместить?**", reply_markup=kb, parse_mode="Markdown")
        await state.set_state(AddPurchase.waiting_move_target)
        return

    elif message.text == "🔙 Назад":
        last_status = data.get("last_list_status", "pending")
        await show_list(message, last_status, state)
        await state.clear()
        return

    elif message.text == "🏠 Главное меню":
        await go_main_menu(message, state)
        return


@router.message(StateFilter(AddPurchase.waiting_delete_confirm))
async def confirm_delete(message: types.Message, state: FSMContext):
    """Подтверждение удаления"""
    data = await state.get_data()
    purchase_id = data.get('pending_delete_id')
    purchase_name = data.get('pending_delete_name', 'товар')

    if "УДАЛИТЬ" in message.text:
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                cursor = await db.execute('SELECT photo_path FROM purchases WHERE id=? AND user_id=?',
                                          (purchase_id, message.from_user.id))
                row = await cursor.fetchone()
                if row and row[0] and os.path.exists(row[0]):
                    os.remove(row[0])

                await db.execute('DELETE FROM purchases WHERE id=? AND user_id=?',
                                 (purchase_id, message.from_user.id))
                await db.commit()

            await message.answer(f"✅ **'{escape_md(purchase_name)}' удалено навсегда!**",
                                 reply_markup=main_keyboard(), parse_mode="Markdown")
        except Exception as e:
            await message.answer("❌ Ошибка удаления!", reply_markup=main_keyboard())
    else:
        await message.answer("✅ Удаление отменено.", reply_markup=main_keyboard())

    await state.clear()


@router.message(StateFilter(AddPurchase.waiting_move_target))
async def process_move_target(message: types.Message, state: FSMContext):
    """Перемещение покупки в другой статус"""
    status_map = {
        "📋 Ждут решения": "pending",
        "✅ Мои покупки": "buy",
        "⏳ Отложенные": "wait",
        "❌ Отказ": "reject"
    }

    if message.text in status_map:
        data = await state.get_data()
        pid = data.get('last_viewed_id')
        if pid:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute('UPDATE purchases SET status=? WHERE id=? AND user_id=?',
                                 (status_map[message.text], pid, message.from_user.id))
                await db.commit()
            await message.answer("✅ Перемещено!", reply_markup=main_keyboard())
    await state.clear()
