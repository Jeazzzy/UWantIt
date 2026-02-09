import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, menu, fsm_steps, blocks, reminders
from database import init_db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    """Запуск бота"""
    await init_db()

    # Подключаем роутеры
    dp.include_router(blocks.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(fsm_steps.router)
    dp.include_router(reminders.router)

    # ✅ Запускаем фоновую проверку напоминаний
    asyncio.create_task(reminders.check_reminders_loop(bot))

    print("✅ Бот запущен!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
