import aiosqlite
from config import DB_NAME

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS purchases
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                price REAL,
                store TEXT,
                link TEXT,
                description TEXT,
                photo_path TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                remind_at TEXT
            )
        ''')
        await db.commit()
