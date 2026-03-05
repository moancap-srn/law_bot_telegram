import aiosqlite
from config import ADMIN_IDS


async def init_db():
    async with aiosqlite.connect("applications.db") as db:
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            username    TEXT,
            name        TEXT NOT NULL,
            phone       TEXT NOT NULL,
            question    TEXT NOT NULL,
            call_time   TEXT NOT NULL,
            status      TEXT DEFAULT 'new',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS admins (
            user_id     INTEGER PRIMARY KEY,
            name        TEXT
        )
        """
        )

        for admin_id in ADMIN_IDS:
            await db.execute(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,)
            )

        await db.commit()
