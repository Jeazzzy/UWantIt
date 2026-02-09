from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_inline_keyboard():
    """Главное меню с inline кнопками"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить покупку", callback_data="add_purchase")],
        [
            InlineKeyboardButton(text="⏳ Ждут решения", callback_data="pending_purchases"),
            InlineKeyboardButton(text="✅ Куплено", callback_data="bought_purchases")
        ],
        [
            InlineKeyboardButton(text="❌ Отменено", callback_data="cancelled_purchases"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        ]
    ])

def list_inline_keyboard():
    """Inline кнопки для списка покупок"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ]
    )

def card_actions_keyboard(purchase_id: int):
    """Inline кнопки для карточки товара"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{purchase_id}"),
                InlineKeyboardButton(text="🔄 Переместить", callback_data=f"move_{purchase_id}")
            ],
            [InlineKeyboardButton(text="🔙 К списку", callback_data="back_to_list")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ]
    )

def move_menu_keyboard(purchase_id: int):
    """Меню перемещения товара"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ждут решения", callback_data=f"moveto_pending_{purchase_id}")],
            [InlineKeyboardButton(text="✅ Куплено", callback_data=f"moveto_buy_{purchase_id}")],
            [InlineKeyboardButton(text="⏳ Отложено", callback_data=f"moveto_wait_{purchase_id}")],
            [InlineKeyboardButton(text="❌ Отказы", callback_data=f"moveto_reject_{purchase_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"open_{purchase_id}")]
        ]
    )

def delete_confirm_keyboard(purchase_id: int):
    """Подтверждение удаления"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ ДА, УДАЛИТЬ", callback_data=f"delete_confirm_{purchase_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"open_{purchase_id}")]
        ]
    )

# ===== REPLY клавиатуры (для ввода текста в FSM) =====

def nav_keyboard(back_text="🔙 Назад", show_main=True):
    """Reply клавиатура для FSM навигации"""
    keyboard = [[KeyboardButton(text=back_text)]]
    if show_main:
        keyboard.append([KeyboardButton(text="🏠 Главное меню")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def skip_keyboard():
    """Reply клавиатура с Пропустить"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

def photo_keyboard():
    """Reply клавиатура для шага с фото"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

def time_keyboard():
    """Reply клавиатура выбора времени"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="5 мин"), KeyboardButton(text="10 мин")],
            [KeyboardButton(text="30 мин"), KeyboardButton(text="1 час")],
            [KeyboardButton(text="6 часов"), KeyboardButton(text="сутки")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def fsm_nav_inline(show_skip=False):
    """Inline навигация для FSM"""
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="fsm_back")]]
    if show_skip:
        buttons.append([InlineKeyboardButton(text="⏭️ Пропустить", callback_data="fsm_skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def fsm_time_inline():
    """Inline кнопки выбора времени"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 мин", callback_data="time_5"),
            InlineKeyboardButton(text="30 мин", callback_data="time_30")
        ],
        [
            InlineKeyboardButton(text="1 час", callback_data="time_60"),
            InlineKeyboardButton(text="6 часов", callback_data="time_360")
        ],
        [
            InlineKeyboardButton(text="1 день", callback_data="time_1440"),
            InlineKeyboardButton(text="3 дня", callback_data="time_4320")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="fsm_back")]
    ])

def main_keyboard():
    """Обычная клавиатура для ПК"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True,
        persistent=True
    )