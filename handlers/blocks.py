from aiogram import types, F, Router
from aiogram.filters import StateFilter
from keyboards import nav_keyboard, skip_keyboard
from states import AddPurchase

router = Router()

# Блокировка файлов в waiting_name
@router.message(StateFilter(AddPurchase.waiting_name),
                F.document | F.photo | F.video | F.voice | F.video_note | F.sticker | F.animation | F.audio)
async def block_files_in_name(message: types.Message):
    """Блокировка файлов при вводе названия"""
    await message.answer(
        "❌ **Только текст!**\n\n"
        "📎 Файлы, фото, видео — **ЗАПРЕЩЕНЫ**\n"
        "✍️ Напиши **название вещи** текстом",
        reply_markup=nav_keyboard(),
        parse_mode="Markdown"
    )

# Блокировка файлов в waiting_price
@router.message(StateFilter(AddPurchase.waiting_price),
                F.document | F.photo | F.video | F.voice | F.video_note | F.sticker | F.animation | F.audio)
async def block_files_in_price(message: types.Message):
    """Блокировка файлов при вводе цены"""
    await message.answer(
        "❌ **Только текст!**\n\n"
        "📎 Файлы, фото, видео — **ЗАПРЕЩЕНЫ**\n"
        "💰 Введи **цену** цифрами (например: 1500 или 1500.50)",
        reply_markup=nav_keyboard(),
        parse_mode="Markdown"
    )

# Блокировка файлов в waiting_store
@router.message(StateFilter(AddPurchase.waiting_store),
                F.document | F.photo | F.video | F.voice | F.video_note | F.sticker | F.animation | F.audio)
async def block_files_in_store(message: types.Message):
    """Блокировка файлов при вводе магазина"""
    await message.answer(
        "❌ **Только текст!**\n\n"
        "📎 Файлы, фото, видео — **ЗАПРЕЩЕНЫ**\n"
        "🏪 Напиши **название магазина** текстом",
        reply_markup=nav_keyboard(),
        parse_mode="Markdown"
    )

# Блокировка файлов в waiting_link_desc
@router.message(StateFilter(AddPurchase.waiting_link_desc),
                F.document | F.photo | F.video | F.voice | F.video_note | F.sticker | F.animation | F.audio)
async def block_files_in_desc(message: types.Message):
    """Блокировка файлов при вводе описания"""
    await message.answer(
        "❌ **Только текст!**\n\n"
        "📎 Файлы, фото, видео — **ЗАПРЕЩЕНЫ**\n"
        "💬 Напиши **только текст** или [Пропустить]",
        reply_markup=skip_keyboard(),
        parse_mode="Markdown"
    )

# Блокировка НЕ-фото в waiting_photo
@router.message(StateFilter(AddPurchase.waiting_photo),
                F.document | F.video | F.voice | F.video_note | F.sticker | F.animation | F.audio)
async def block_non_photo(message: types.Message):
    """Блокировка не-фото файлов на шаге с фото"""
    from keyboards import photo_keyboard
    await message.answer(
        "❌Только ФОТО вещи!\n\n"
        "📎 PDF, ZIP, DOC, видео — ЗАПРЕЩЕНЫ\n"
        "📷 Отправь **только фото** или [Пропустить]",
        reply_markup=photo_keyboard(),
        parse_mode="Markdown"
    )

# Блокировка текста в waiting_photo (кроме "Пропустить")
@router.message(StateFilter(AddPurchase.waiting_photo), F.text)
async def block_text_in_photo(message: types.Message):
    """Блокировка текста на шаге с фото (кроме Пропустить)"""
    from keyboards import photo_keyboard
    if message.text not in ["Пропустить", "🔙 Назад", "🏠 Главное меню"]:
        await message.answer(
            "❌ **Только ФОТО или 'Пропустить'!**\n\n"
            "📷 Отправь **фото вещи**\n"
            "или нажми **[Пропустить]**",
            reply_markup=photo_keyboard(),
            parse_mode="Markdown"
        )
