import asyncio
import aiosqlite
import os
from datetime import datetime, timedelta
from aiogram import Bot, types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from config import DB_NAME
from keyboards import main_inline_keyboard
from states import WaitAgain

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

                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="✅ Да, куплю", callback_data=f"buy_{purchase_id}"),
                            types.InlineKeyboardButton(text="❌ Передумал", callback_data=f"cancel_{purchase_id}")
                        ],
                        [
                            types.InlineKeyboardButton(text="⏳ Подождать еще", callback_data=f"wait_{purchase_id}")
                        ]
                    ])

                    try:
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

                        await db.execute('UPDATE purchases SET reminded = 1 WHERE id = ?', (purchase_id,))
                        await db.commit()
                    except Exception as e:
                        print(f"Ошибка отправки напоминания: {e}")

        except Exception as e:
            print(f"Ошибка в check_reminders_loop: {e}")

        await asyncio.sleep(10)


@router.callback_query(F.data.startswith("buy_"))
async def buy_callback(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь купил"""
    await state.clear()
    purchase_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status = "bought" WHERE id = ?', (purchase_id,))
        await db.commit()

    await callback.message.delete()
    await callback.answer("✅ Покупка завершена!")


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь передумал"""
    await state.clear()
    purchase_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE purchases SET status = "cancelled" WHERE id = ?', (purchase_id,))
        await db.commit()

    await callback.message.delete()
    await callback.answer("❌ Покупка отменена!")


@router.callback_query(F.data.startswith("wait_"))
async def wait_callback(callback: types.CallbackQuery, state: FSMContext):
    """Подождать еще - выбор нового времени"""
    purchase_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT name, price FROM purchases WHERE id = ?',
            (purchase_id,)
        )
        purchase = await cursor.fetchone()

    if not purchase:
        await callback.answer("❌ Покупка не найдена!")
        return

    name, price = purchase

    # ✅ Клавиатура выбора времени
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="5 мин", callback_data=f"waittime_{purchase_id}_5"),
            types.InlineKeyboardButton(text="30 мин", callback_data=f"waittime_{purchase_id}_30")
        ],
        [
            types.InlineKeyboardButton(text="1 час", callback_data=f"waittime_{purchase_id}_60"),
            types.InlineKeyboardButton(text="6 часов", callback_data=f"waittime_{purchase_id}_360")
        ],
        [
            types.InlineKeyboardButton(text="1 день", callback_data=f"waittime_{purchase_id}_1440"),
            types.InlineKeyboardButton(text="3 дня", callback_data=f"waittime_{purchase_id}_4320")
        ],
        [
            types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{purchase_id}")
        ]
    ])

    text = (
        f"⏳ **Подождать еще?**\n\n"
        f"📦 **{name}**\n"
        f"💰 {price:,.0f}₽\n\n"
        f"Выбери время или напиши минуты (например: `15`, `120`)"
    )

    # ✅ Сохраняем purchase_id и message_id для обработки текста
    await state.update_data(
        purchase_id=purchase_id,
        wait_message_id=callback.message.message_id
    )
    await state.set_state(WaitAgain.waiting_time)

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("waittime_"))
async def waittime_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора нового времени кнопкой"""
    await state.clear()
    parts = callback.data.split("_")
    purchase_id = int(parts[1])
    minutes = int(parts[2])

    new_remind_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE purchases SET remind_at = ?, reminded = 0 WHERE id = ?',
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

    await callback.answer(f"⏳ Напомню через {time_str}!")


# ✅ НОВОЕ: Обработка текстового ввода минут
@router.message(StateFilter(WaitAgain.waiting_time))
async def process_wait_time_text(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка ввода минут текстом (для откладывания и перемещения)"""
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError()
    except ValueError:
        warning = await message.answer(
            "❌ **Неверное время!**\n\n"
            "Введи число минут (например: `15`, `120`)",
            parse_mode="Markdown"
        )
        await message.delete()
        await asyncio.sleep(3)
        await warning.delete()
        return

    data = await state.get_data()

    # ✅ Проверяем: это откладывание или перемещение
    if 'move_purchase_id' in data:
        # Перемещение
        purchase_id = data['move_purchase_id']
        move_message_id = data['move_message_id']

        new_remind_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                'UPDATE purchases SET status = "pending", remind_at = ?, reminded = 0 WHERE id = ?',
                (new_remind_at, purchase_id)
            )
            await db.commit()

        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=move_message_id)
        except:
            pass

        await message.delete()
        await state.clear()

        confirm = await message.answer(f"✅ Перемещено! Напомню через {minutes} мин!")
        await asyncio.sleep(3)
        await confirm.delete()

    else:
        # Откладывание (старая логика)
        purchase_id = data['purchase_id']
        wait_message_id = data['wait_message_id']

        new_remind_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                'UPDATE purchases SET remind_at = ?, reminded = 0 WHERE id = ?',
                (new_remind_at, purchase_id)
            )
            await db.commit()

        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=wait_message_id)
        except:
            pass

        await message.delete()
        await state.clear()

        confirm = await message.answer(f"⏳ Напомню через {minutes} мин!")
        await asyncio.sleep(3)
        await confirm.delete()