import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import db

# handlers
from handlers import table


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    await db.create_pool()

    dp.include_router(table.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())