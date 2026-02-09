import re
import os
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import types, F, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from keyboards import fsm_nav_inline, fsm_time_inline, main_inline_keyboard
from states import AddPurchase
from config import DB_NAME

router = Router()


# Сохраняем ID сообщения формы
async def update_form_message(message_or_callback, text: str, reply_markup, state: FSMContext):
    """Обновление сообщения формы"""
    data = await state.get_data()
    form_message_id = data.get('form_message_id')

    # Если это callback - редактируем
    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return message_or_callback.message.message_id

    # Если есть старое сообщение формы - редактируем его
    if form_message_id:
        try:
            await message_or_callback.bot.edit_message_text(
                text=text,
                chat_id=message_or_callback.chat.id,
                message_id=form_message_id,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            # Удаляем сообщение пользователя
            await message_or_callback.delete()
            return form_message_id
        except:
            pass

    # Иначе создаём новое
    await message_or_callback.delete()
    sent = await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode="Markdown")
    return sent.message_id


@router.message(StateFilter(AddPurchase.waiting_name))
async def process_name(message: types.Message, state: FSMContext):
    """Обработка названия вещи"""
    if not re.match(r'^[а-яёА-ЯЁa-zA-Z0-9\s\-_.,!?()]+$', message.text.strip()):
        warning = await message.answer(
            "❌ **Неверное название!**\n\n"
            "Используй только буквы, цифры и символы.",
            parse_mode="Markdown"
        )
        await message.delete()
        await asyncio.sleep(3)
        await warning.delete()
        return

    await state.update_data(name=message.text.strip())
    message_id = await update_form_message(
        message,
        f"📝 **Добавление покупки**\n\n"
        f"✅ Название: `{message.text.strip()}`\n\n"
        f"Шаг 2/6: Введи **цену вещи** (₽)\n\n"
        f"💡 Примеры: `1500`, `1 000 000`, `1.500.000`",
        fsm_nav_inline(),
        state
    )
    await state.update_data(form_message_id=message_id)
    await state.set_state(AddPurchase.waiting_price)


@router.message(StateFilter(AddPurchase.waiting_price))
async def process_price(message: types.Message, state: FSMContext):
    """Обработка цены"""
    cleaned = ''.join(c for c in message.text if c.isdigit() or c in '., ')
    cleaned = cleaned.replace(' ', '').replace(',', '.')

    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]

    try:
        price = float(cleaned) if cleaned else 0
        if price <= 0:
            raise ValueError()
    except ValueError:
        warning = await message.answer(
            "❌ **Неверная цена!**\n\n"
            "Введи число. Примеры:\n"
            "• `1500`\n"
            "• `1 000 000`\n"
            "• `1.500.000`",
            parse_mode="Markdown"
        )
        await message.delete()
        await asyncio.sleep(3)
        await warning.delete()
        return

    data = await state.get_data()
    await state.update_data(price=price)
    message_id = await update_form_message(
        message,
        f"📝 **Добавление покупки**\n\n"
        f"✅ Название: `{data['name']}`\n"
        f"✅ Цена: `{price:,.0f}₽`\n\n"
        f"Шаг 3/6: Введи **название магазина**",
        fsm_nav_inline(),
        state
    )
    await state.update_data(form_message_id=message_id)
    await state.set_state(AddPurchase.waiting_store)


@router.message(StateFilter(AddPurchase.waiting_store))
async def process_store(message: types.Message, state: FSMContext):
    """Обработка магазина"""
    data = await state.get_data()
    await state.update_data(store=message.text.strip())
    message_id = await update_form_message(
        message,
        f"📝 **Добавление покупки**\n\n"
        f"✅ Название: `{data['name']}`\n"
        f"✅ Цена: `{data['price']:,.0f}₽`\n"
        f"✅ Магазин: `{message.text.strip()}`\n\n"
        f"Шаг 4/6: Введи **ссылку или описание**",
        fsm_nav_inline(show_skip=True),
        state
    )
    await state.update_data(form_message_id=message_id)
    await state.set_state(AddPurchase.waiting_link_desc)


@router.message(StateFilter(AddPurchase.waiting_link_desc))
async def process_link_desc(message: types.Message, state: FSMContext):
    """Обработка описания"""
    data = await state.get_data()
    await state.update_data(link_desc_text=message.text.strip())
    message_id = await update_form_message(
        message,
        f"📝 **Добавление покупки**\n\n"
        f"✅ Название: `{data['name']}`\n"
        f"✅ Цена: `{data['price']:,.0f}₽`\n"
        f"✅ Магазин: `{data['store']}`\n"
        f"✅ Описание: `{message.text.strip()[:30]}...`\n\n"
        f"Шаг 5/6: Отправь **фото вещи**\n\n"
        f"📷 Только изображения!",
        fsm_nav_inline(show_skip=True),
        state
    )
    await state.update_data(form_message_id=message_id)
    await state.set_state(AddPurchase.waiting_photo)


@router.message(StateFilter(AddPurchase.waiting_delay))
async def process_delay_text(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка ввода минут текстом"""
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError()
    except ValueError:
        warning = await message.answer(
            "❌ **Неверное время!**\n\n"
            "Введи число минут (например: `5`, `30`, `1440`)\n"
            "Или выбери кнопкой выше.",
            parse_mode="Markdown"
        )
        await message.delete()
        await asyncio.sleep(3)
        await warning.delete()
        return

    # Сохраняем покупку
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
                         ''', (message.from_user.id, data['name'], data['price'], data['store'],
                               data.get('link_desc_text'), data.get('link_desc_text'),
                               data.get('photo_path'), remind_at, datetime.now().isoformat()))
        await db.commit()

    # Обновляем сообщение формы
    form_message_id = data.get('form_message_id')
    if form_message_id:
        try:
            await bot.edit_message_text(
                text=f"✅ **Покупка добавлена!**\n\n"
                     f"📦 {data['name']}\n"
                     f"💰 {data['price']:,.0f}₽\n"
                     f"🏪 {data['store']}\n\n"
                     f"⏰ Напомню через {minutes} мин!",
                chat_id=message.chat.id,
                message_id=form_message_id,
                reply_markup=main_inline_keyboard(),
                parse_mode="Markdown"
            )
        except:
            pass

    await message.delete()
    await state.clear()


@router.message(StateFilter(AddPurchase.waiting_photo), F.photo)
async def process_photo(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка фото"""
    photo = message.photo[-1]
    user_id = message.from_user.id
    file = await bot.get_file(photo.file_id)
    photo_path = f"photos/{user_id}_{photo.file_id}.jpg"
    Path("photos").mkdir(exist_ok=True)
    await bot.download_file(file.file_path, photo_path)
    await state.update_data(photo_path=photo_path)

    data = await state.get_data()
    message_id = await update_form_message(
        message,
        f"📝 **Добавление покупки**\n\n"
        f"✅ Название: `{data['name']}`\n"
        f"✅ Цена: `{data['price']:,.0f}₽`\n"
        f"✅ Магазин: `{data['store']}`\n"
        f"✅ Фото: загружено\n\n"
        f"Шаг 6/6: Выбери **задержку до напоминания**\n"
        f"💡 Можно выбрать кнопкой или написать минуты (например: `30`)",
        fsm_time_inline(),
        state
    )
    await state.update_data(form_message_id=message_id)
    await state.set_state(AddPurchase.waiting_delay)
