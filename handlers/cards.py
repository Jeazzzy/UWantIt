import os
import aiosqlite
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from keyboards import card_actions_keyboard, move_menu_keyboard, delete_confirm_keyboard, main_inline_keyboard
from utils import escape_md
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
        await callback.message.edit_text(
            "❌ Товар не найден!",
            reply_markup=main_inline_keyboard()
        )
        return

    text = f"📦 **{escape_md(row[0])}**\n💰 {row[1]:,.0f}₽\n🏪 {escape_md(row[2])}"
    if row[4]:  # description
        text += f"\n\n{escape_md(row[4])}"
    if row[3]:  # link
        text += f"\n\n🔗 {escape_md(row[3])}"

    kb = card_actions_keyboard(purchase_id)

    # Если есть фото - отправляем новое сообщение с фото
    if row[5] and os.path.exists(row[5]):
        await callback.message.delete()
        await callback.bot.send_photo(
            callback.from_user.id,
            FSInputFile(row[5]),
            caption=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        # Иначе редактируем текущее
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    await callback.answer()


@router.callback_query(F.data.startswith("move_"))
async def move_purchase_callback(callback: types.CallbackQuery):
    """Показ меню перемещения"""
    purchase_id = int(callback.data.split("_")[1])

    # Получаем название товара
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT name FROM purchases WHERE id=? AND user_id=?',
            (purchase_id, callback.from_user.id)
        )
        row = await cursor.fetchone()

    if row:
        text = f"🔄 **Переместить покупку**\n\n📦 {escape_md(row[0])}\n\nКуда переместить?"
        await callback.message.edit_text(
            text,
            reply_markup=move_menu_keyboard(purchase_id),
            parse_mode="Markdown"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("moveto_"))
async def moveto_callback(callback: types.CallbackQuery):
    """Перемещение покупки"""
    parts = callback.data.split("_")
    status = parts[1]  # pending/buy/wait/reject
    purchase_id = int(parts[2])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE purchases SET status=? WHERE id=? AND user_id=?',
            (status, purchase_id, callback.from_user.id)
        )
        await db.commit()

    await callback.answer("✅ Перемещено!")

    # Возвращаемся к карточке
    await open_purchase_callback(callback,
                                 await callback.bot.fsm.get_context(bot=callback.bot, user_id=callback.from_user.id,
                                                                    chat_id=callback.message.chat.id))


@router.callback_query(F.data.startswith("delete_") & ~F.data.startswith("delete_confirm_"))
async def delete_purchase_callback(callback: types.CallbackQuery):
    """Запрос подтверждения удаления"""
    purchase_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT name FROM purchases WHERE id=? AND user_id=?',
            (purchase_id, callback.from_user.id)
        )
        row = await cursor.fetchone()

    if row:
        text = (
            f"🗑️ **Подтверждение удаления**\n\n"
            f"📦 {escape_md(row[0])}\n\n"
            f"⚠️ Уверен, что хочешь **НАВСЕГДА** удалить эту покупку?"
        )
        await callback.message.edit_text(
            text,
            reply_markup=delete_confirm_keyboard(purchase_id),
            parse_mode="Markdown"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_confirm_"))
async def delete_confirm_callback(callback: types.CallbackQuery, state: FSMContext):
    """Окончательное удаление"""
    purchase_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT photo_path, name FROM purchases WHERE id=? AND user_id=?',
            (purchase_id, callback.from_user.id)
        )
        row = await cursor.fetchone()

        if row:
            # Удаляем фото
            if row[0] and os.path.exists(row[0]):
                os.remove(row[0])

            # Удаляем запись
            await db.execute(
                'DELETE FROM purchases WHERE id=? AND user_id=?',
                (purchase_id, callback.from_user.id)
            )
            await db.commit()

            await callback.message.edit_text(
                f"✅ **Удалено!**\n\n📦 {escape_md(row[1])}",
                reply_markup=main_inline_keyboard(),
                parse_mode="Markdown"
            )
            await callback.answer("🗑️ Удалено!")
        else:
            await callback.answer("❌ Не найдено", show_alert=True)
