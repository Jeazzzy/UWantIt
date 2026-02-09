from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    """Главное меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Добавить покупку")],
            [KeyboardButton(text="📋 Ждут решения"), KeyboardButton(text="✅ Мои покупки")],
            [KeyboardButton(text="⏳ Отложенные"), KeyboardButton(text="❌ Отказ")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def nav_keyboard(back_text="🔙 Назад", show_main=True):
    """Навигационная клавиатура с кнопкой Назад"""
    keyboard = [[KeyboardButton(text=back_text)]]
    if show_main:
        keyboard.append([KeyboardButton(text="🏠 Главное меню")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def skip_keyboard():
    """Клавиатура с кнопкой Пропустить"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

def photo_keyboard():
    """Клавиатура для шага с фото"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

def time_keyboard():
    """Клавиатура с выбором времени задержки"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="5 мин"), KeyboardButton(text="10 мин")],
            [KeyboardButton(text="30 мин"), KeyboardButton(text="1 час")],
            [KeyboardButton(text="6 часов"), KeyboardButton(text="сутки")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
