import aiosqlite
from config import DB_NAME


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей
        await db.execute('''
                         CREATE TABLE IF NOT EXISTS users
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             user_id
                             INTEGER
                             UNIQUE
                             NOT
                             NULL,
                             created_at
                             TIMESTAMP
                             DEFAULT
                             CURRENT_TIMESTAMP
                         )
                         ''')

        # Таблица покупок
        await db.execute('''
                         CREATE TABLE IF NOT EXISTS purchases
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             user_id
                             INTEGER
                             NOT
                             NULL,
                             name
                             TEXT
                             NOT
                             NULL,
                             price
                             REAL
                             NOT
                             NULL,
                             store
                             TEXT,
                             link
                             TEXT,
                             description
                             TEXT,
                             photo_path
                             TEXT,
                             remind_at
                             TIMESTAMP,
                             reminded
                             INTEGER
                             DEFAULT
                             0,
                             status
                             TEXT
                             DEFAULT
                             'pending',
                             created_at
                             TIMESTAMP
                             DEFAULT
                             CURRENT_TIMESTAMP,
                             FOREIGN
                             KEY
                         (
                             user_id
                         ) REFERENCES users
                         (
                             user_id
                         )
                             )
                         ''')

        # ✅ Проверяем и добавляем отсутствующие столбцы
        cursor = await db.execute("PRAGMA table_info(purchases)")
        columns = [row[1] for row in await cursor.fetchall()]

        if 'reminded' not in columns:
            await db.execute('ALTER TABLE purchases ADD COLUMN reminded INTEGER DEFAULT 0')
            print("✅ Добавлен столбец 'reminded'")

        if 'status' not in columns:
            await db.execute('ALTER TABLE purchases ADD COLUMN status TEXT DEFAULT "pending"')
            print("✅ Добавлен столбец 'status'")

        await db.commit()
        print("✅ База данных инициализирована")
