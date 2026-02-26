import aiosqlite
from config import DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # جدول المستخدمين
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            level INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0,
            join_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # جدول نقاط الألعاب لكل لعبة
        await db.execute('''CREATE TABLE IF NOT EXISTS game_points (
            user_id INTEGER,
            chat_id INTEGER,
            game_name TEXT,
            points INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, chat_id, game_name)
        )''')

        # جدول الروليت
        await db.execute('''CREATE TABLE IF NOT EXISTS roulette (
            chat_id INTEGER,
            user_id INTEGER,
            roulette_points INTEGER DEFAULT 0,
            roulette_titles INTEGER DEFAULT 0,
            PRIMARY KEY(chat_id, user_id)
        )''')

        # جدول سجل الروليت
        await db.execute('''CREATE TABLE IF NOT EXISTS roulette_history (
            round_number INTEGER,
            chat_id INTEGER,
            winner_name TEXT,
            winner_id INTEGER,
            participants_count INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # جدول البنك
        await db.execute('''CREATE TABLE IF NOT EXISTS bank (
            user_id INTEGER,
            chat_id INTEGER,
            balance INTEGER DEFAULT 10000000,
            last_salary INTEGER DEFAULT 0,
            last_investment INTEGER DEFAULT 0
        )''')

        await db.commit()
