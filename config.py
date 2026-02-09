import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

Path("photos").mkdir(exist_ok=True)
Path("docs").mkdir(exist_ok=True)
DB_NAME = 'impulse_bot.db'
