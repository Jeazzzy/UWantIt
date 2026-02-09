import asyncio
import aiosqlite
import os
from datetime import datetime
from aiogram import Bot, types, Router, F
from config import DB_NAME
from keyboards import main_inline_keyboard

router = Router()


async def check_reminders_loop(bot: Bot):
    """Фоновая задача проверки напоминаний"""
    while True:
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                now = datetime.now().isoformat()
                cursor = await db.execute(
                    'SELECT id, user_id, name, price, store, link, description, photo_path FROM purchases WHERE remind_at <= ? AND reminded = 0',
                    (now,)
                )
                purchases = await cursor.fetchall()

                for p in purchases:
                    purchase_id, user_id, name, price, store, link, desc, photo_path = p

                    # Формируем текст напоминания
                    text = (
                        f"⏰ **Напоминание о покупке!**\n\n"
                        f"📦 **{name}**\n"
                        f"💰 {price:,.0f}₽\n"
                        f"🏪 {store}\n"
                    )

                    if desc:
                        text += f"📝 {desc}\n"

                    if link:
                        text += f"🔗 [Ссылка]({link})\n"

                    text += "\n❓ Всё ещё хочешь купить?"

                    # Клавиатура
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="✅ Да, куплю", callback_data=f"buy_{purchase_id}"),
                            types.InlineKeyboardButton(text="❌ Нет, передумал", callback_data=f"cancel_{purchase_id}")
                        ]
                    ])

                    try:
                        # ✅ Проверяем существование файла
                        if photo_path and os.path.exists(photo_path):
                            await bot.send_photo(
                                chat_id=user_id,
                                photo=types.FSInputFile(photo_path),
                                caption=text,
                                reply_markup=keyboard,
                                parse_mode="Markdown"
                            )
                        else:
                            await bot.send_message(
                                chat_id=user_id,
                                text=text,
                                reply_markup=keyboard,
                                parse_mode="Markdown"
                            )

                        # Отмечаем как отправленное
                        await db.execute('UPDATE purchases SET reminded = 1 WHERE id = ?', (purchase_id,))
                        await db.commit()
                    except Exception as e:
                        print(f"Ошибка отправки напоминания: {e}")

        except Exception as e:
            print(f"Ошибка в check_reminders_loop: {e}")

        await asyncio.sleep(10)  # Проверяем каждые 10 секунд


@router.callback_query(F.data.startswith("buy_"))
async def buy_callback(callback: types.CallbackQuery):
    """Пользователь купил"""
    purchase_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status = "bought" WHERE id = ?', (purchase_id,))
        await db.commit()

    # ✅ Проверяем тип сообщения
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n✅ **Отмечено как купленное**",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text=callback.message.text + "\n\n✅ **Отмечено как купленное**",
            parse_mode="Markdown"
        )

    await callback.answer("✅ Покупка завершена!")


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_callback(callback: types.CallbackQuery):
    """Пользователь передумал"""
    purchase_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status = "cancelled" WHERE id = ?', (purchase_id,))
        await db.commit()

    # ✅ Проверяем тип сообщения
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n❌ **Покупка отменена**",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text=callback.message.text + "\n\n❌ **Покупка отменена**",
            parse_mode="Markdown"
        )

    await callback.answer("❌ Покупка отменена!")
