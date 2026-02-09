import re
import os
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import types, F, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from keyboards import nav_keyboard, skip_keyboard, photo_keyboard, time_keyboard, main_keyboard
from states import AddPurchase
from config import DB_NAME

router = Router()


@router.message(StateFilter(AddPurchase.waiting_name))
async def process_name(message: types.Message, state: FSMContext):
    """Обработка названия вещи"""
    from handlers.menu import go_main_menu

    if message.text in ["🔙 Назад", "🏠 Главное меню"]:
        await go_main_menu(message, state)
        return
    if not re.match(r'^[а-яёА-ЯЁa-zA-Z0-9\s\-_.,!?()]+$', message.text.strip()):
        await message.answer("❌ Неверное название! Используй только буквы, цифры и символы.",
                             reply_markup=nav_keyboard())
        return
    await state.update_data(name=message.text.strip())
    await message.answer("💰 Введи цену вещи:", reply_markup=nav_keyboard())
    await state.set_state(AddPurchase.waiting_price)


@router.message(StateFilter(AddPurchase.waiting_price))
async def process_price(message: types.Message, state: FSMContext):
    """Обработка цены"""
    from handlers.menu import go_main_menu

    if message.text in ["🔙 Назад"]:
        await message.answer("Название вещи?", reply_markup=nav_keyboard())
        await state.set_state(AddPurchase.waiting_name)
        return
    if message.text in ["🏠 Главное меню"]:
        await go_main_menu(message, state)
        return

    cleaned = ''.join(c for c in message.text if c.isdigit() or c in '.,').replace(',', '.')
    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    try:
        price = float(cleaned)
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Неверная цена! Введи число.", reply_markup=nav_keyboard())
        return

    await state.update_data(price=price)
    await message.answer("🏪 Магазин?", reply_markup=nav_keyboard())
    await state.set_state(AddPurchase.waiting_store)


@router.message(StateFilter(AddPurchase.waiting_store))
async def process_store(message: types.Message, state: FSMContext):
    """Обработка названия магазина"""
    from handlers.menu import go_main_menu

    if message.text in ["🔙 Назад"]:
        await message.answer("💰 Цена вещи:", reply_markup=nav_keyboard())
        await state.set_state(AddPurchase.waiting_price)
        return
    if message.text in ["🏠 Главное меню"]:
        await go_main_menu(message, state)
        return

    await state.update_data(store=message.text.strip())
    await message.answer("🔗 Ссылка или описание (только текст):", reply_markup=skip_keyboard())
    await state.set_state(AddPurchase.waiting_link_desc)


@router.message(StateFilter(AddPurchase.waiting_link_desc))
async def process_link_desc(message: types.Message, state: FSMContext):
    """Обработка ссылки/описания"""
    from handlers.menu import go_main_menu

    if message.text in ["🔙 Назад", "🏠 Главное меню", "Пропустить"]:
        if message.text == "🔙 Назад":
            await message.answer("🏪 Магазин?", reply_markup=nav_keyboard())
            await state.set_state(AddPurchase.waiting_store)
        elif message.text == "🏠 Главное меню":
            await go_main_menu(message, state)
        else:  # Пропустить
            await state.update_data(link_desc_text=None)
            await message.answer("📷 Фото вещи? (отправь фото или пропусти)", reply_markup=photo_keyboard())
            await state.set_state(AddPurchase.waiting_photo)
        return

    await state.update_data(link_desc_text=message.text.strip())
    await message.answer("📷 Фото вещи? (отправь фото или пропусти)", reply_markup=photo_keyboard())
    await state.set_state(AddPurchase.waiting_photo)


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
    await message.answer("Фото сохранено.")
    await ask_delay(message, state)


@router.message(StateFilter(AddPurchase.waiting_photo), F.text == "Пропустить")
async def skip_photo_btn(message: types.Message, state: FSMContext):
    """Пропуск фото"""
    await state.update_data(photo_path=None)
    await ask_delay(message, state)


async def ask_delay(message: types.Message, state: FSMContext):
    """Запрос задержки для напоминания"""
    await message.answer("Задержка до напоминания?", reply_markup=time_keyboard())
    await state.set_state(AddPurchase.waiting_delay)


@router.message(StateFilter(AddPurchase.waiting_delay))
async def process_delay(message: types.Message, state: FSMContext):
    """Обработка выбора задержки и сохранение в БД"""
    time_map = {"5 мин": 5, "10 мин": 10, "30 мин": 30, "1 час": 60, "6 часов": 360, "сутки": 1440}

    text = message.text.lower().strip()
    minutes = time_map.get(text)

    if minutes is None:
        numbers = re.findall(r'\d+', text)
        if numbers:
            try:
                num = int(numbers[0])
                if "час" in text:
                    minutes = num * 60
                elif "мин" in text:
                    minutes = num
                elif "сут" in text:
                    minutes = num * 1440
                else:
                    minutes = num
            except:
                pass

    if minutes is None or minutes <= 0:
        await message.answer("❌ Неверный формат! Выбери кнопку.", reply_markup=nav_keyboard())
        return

    data = await state.get_data()
    remind_at = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
                         INSERT INTO purchases (user_id, name, price, store, link, description, photo_path, remind_at,
                                                created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         ''', (message.from_user.id, data['name'], data['price'], data['store'],
                               data.get('link_desc_text'), data.get('link_desc_text'),
                               data.get('photo_path'), remind_at, datetime.now().isoformat()))
        cursor = await db.execute('SELECT last_insert_rowid()')
        purchase_id = (await cursor.fetchone())[0]
        await db.commit()

    await message.answer("✅ Добавлено! Напомню через время.", reply_markup=main_keyboard())
    await state.clear()

    # Запуск напоминания
    from handlers.reminders import check_reminder
    asyncio.create_task(check_reminder(message.from_user.id, purchase_id, message.bot))
