import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import start, menu, blocks, fsm_steps, lists, cards, reminders

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация роутеров (ПОРЯДОК ВАЖЕН!)
dp.include_router(start.router)
dp.include_router(menu.router)
dp.include_router(blocks.router)       # Блокировщики ПЕРЕД fsm_steps
dp.include_router(fsm_steps.router)
dp.include_router(lists.router)
dp.include_router(cards.router)
dp.include_router(reminders.router)

async def main():
    """Запуск бота"""
    await init_db()
    print("✅ Бот запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
