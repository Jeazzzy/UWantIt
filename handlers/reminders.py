import os
import asyncio
import aiosqlite
from datetime import datetime
from aiogram import types, F, Router, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from keyboards import main_keyboard
from utils import escape_md
from config import DB_NAME

router = Router()


async def check_reminder(user_id: int, purchase_id: int, bot: Bot):
    """Проверка и отправка напоминания"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT remind_at FROM purchases WHERE id=?', (purchase_id,))
        row = await cursor.fetchone()
        if row:
            remind_time = datetime.fromisoformat(row[0])
            seconds = (remind_time - datetime.now()).total_seconds()
            if seconds > 0:
                await asyncio.sleep(seconds)

            cursor = await db.execute(
                'SELECT id, name, price, store, description, link, photo_path FROM purchases WHERE id=? AND user_id=? AND status="pending"',
                (purchase_id, user_id)
            )
            row = await cursor.fetchone()
            if row:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Купить", callback_data=f"dec_buy_{row[0]}")],
                        [InlineKeyboardButton(text="⏳ Подождать", callback_data=f"dec_wait_{row[0]}")],
                        [InlineKeyboardButton(text="❌ Не нравится", callback_data=f"dec_reject_{row[0]}")]
                    ]
                )
                text = f"⏰ Напоминание!\n📦 **{escape_md(row[1])}**\n💰 {row[2]:,.0f}₽\n🏪 {escape_md(row[3])}"
                if row[5]:  # link
                    text += f"\n🔗 {escape_md(row[5])}"
                if row[4]:  # description
                    text += f"\n\n{escape_md(row[4])}"

                if row[6] and os.path.exists(row[6]):  # photo_path
                    await bot.send_photo(user_id, FSInputFile(row[6]), caption=text, reply_markup=kb,
                                         parse_mode="Markdown")
                else:
                    await bot.send_message(user_id, text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("dec_buy_"))
async def buy_decision_callback(callback: types.CallbackQuery):
    """Решение: Купить"""
    purchase_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status="buy" WHERE id=? AND user_id=?',
                         (purchase_id, callback.from_user.id))
        await db.commit()

    if callback.message.photo:
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n✅ Отмечено как 'Куплено!'",
                parse_mode="Markdown"
            )
        else:
            await callback.message.delete()
            await callback.message.answer("✅ Куплено!", reply_markup=main_keyboard())
    else:
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Отмечено как 'Куплено!'",
            parse_mode="Markdown"
        )
    await callback.answer("✅ Куплено!")


@router.callback_query(F.data.startswith("dec_wait_"))
async def wait_decision_callback(callback: types.CallbackQuery):
    """Решение: Подождать"""
    purchase_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status="wait" WHERE id=? AND user_id=?',
                         (purchase_id, callback.from_user.id))
        await db.commit()

    if callback.message.photo:
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n⏳ Отложено!",
                parse_mode="Markdown"
            )
        else:
            await callback.message.delete()
            await callback.message.answer("⏳ Отложено!", reply_markup=main_keyboard())
    else:
        await callback.message.edit_text(
            callback.message.text + "\n\n⏳ Отложено!",
            parse_mode="Markdown"
        )
    await callback.answer("⏳ Отложено!")


@router.callback_query(F.data.startswith("dec_reject_"))
async def reject_decision_callback(callback: types.CallbackQuery):
    """Решение: Отклонить"""
    purchase_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT photo_path FROM purchases WHERE id=? AND user_id=?',
                                  (purchase_id, callback.from_user.id))
        row = await cursor.fetchone()
        if row and row[0] and os.path.exists(row[0]):
            os.remove(row[0])
        await db.execute('DELETE FROM purchases WHERE id=? AND user_id=?',
                         (purchase_id, callback.from_user.id))
        await db.commit()

    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("❌ Отклонено!", reply_markup=main_keyboard())
    await callback.answer("❌ Отклонено!")
