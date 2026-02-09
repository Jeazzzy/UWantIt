import asyncio
from aiogram import types, F, Router
from aiogram.filters import StateFilter
from states import AddPurchase

router = Router()

# ===== ГЛОБАЛЬНЫЕ БЛОКИРОВЩИКИ (работают везде) =====

@router.message(F.sticker | F.animation | F.video_note | F.voice)
async def block_forbidden_content(message: types.Message):
    """Блокировка стикеров, гифок, кружков, голосовых"""
    await message.delete()
    warning = await message.answer(
        "❌ **Запрещено!**\n\n"
        "🚫 Стикеры, гифки, кружки, голосовые сообщения не принимаются.",
        parse_mode="Markdown"
    )
    await asyncio.sleep(3)
    await warning.delete()

# ===== БЛОКИРОВЩИКИ ДЛЯ FSM СОСТОЯНИЙ =====

# Блокировка всех НЕ-текстовых в текстовых полях
@router.message(
    StateFilter(AddPurchase.waiting_name, AddPurchase.waiting_store, AddPurchase.waiting_link_desc),
    F.document | F.photo | F.video | F.audio
)
async def block_files_in_text_fields(message: types.Message):
    """Блокировка файлов в текстовых полях"""
    await message.delete()
    warning = await message.answer(
        "❌ **Только текст!**\n\n"
        "📎 Файлы, фото, видео запрещены в этом поле.",
        parse_mode="Markdown"
    )
    await asyncio.sleep(3)
    await warning.delete()

# Блокировка всех НЕ-текстовых в поле цены
@router.message(
    StateFilter(AddPurchase.waiting_price),
    F.document | F.photo | F.video | F.audio
)
async def block_files_in_price(message: types.Message):
    """Блокировка файлов в поле цены"""
    await message.delete()
    warning = await message.answer(
        "❌ **Только текст с цифрами!**\n\n"
        "📎 Файлы запрещены. Введи цену числом.",
        parse_mode="Markdown"
    )
    await asyncio.sleep(3)
    await warning.delete()

# Блокировка НЕ-фото в поле фото
@router.message(
    StateFilter(AddPurchase.waiting_photo),
    F.document | F.video | F.audio
)
async def block_non_photo_files(message: types.Message):
    """Блокировка не-фото файлов"""
    await message.delete()
    warning = await message.answer(
        "❌ **Только фото!**\n\n"
        "📎 PDF, ZIP, DOC, видео запрещены.\n"
        "📷 Отправь **только изображение** или нажми **Пропустить**.",
        parse_mode="Markdown"
    )
    await asyncio.sleep(3)
    await warning.delete()

# Блокировка ВСЕХ файлов/фото в состоянии выбора задержки
@router.message(
    StateFilter(AddPurchase.waiting_delay),
    F.document | F.photo | F.video | F.audio
)
async def block_files_in_delay(message: types.Message):
    """Блокировка файлов при выборе задержки"""
    await message.delete()
    warning = await message.answer(
        "❌ **Файлы запрещены!**\n\n"
        "⏱️ Выбери время кнопками выше.",
        parse_mode="Markdown"
    )
    await asyncio.sleep(3)
    await warning.delete()