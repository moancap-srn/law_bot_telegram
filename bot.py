import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db
from handlers import client, admin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    await init_db()
    dp.include_router(client.router)

    dp.include_router(admin.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
