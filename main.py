import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import db

# handlers
from handlers import table
from handlers import user   # ⬅️ yangi qo'shildi

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    await db.create_pool()

    # routerlar
    dp.include_router(user.router)   # ⬅️ /start inline menu
    dp.include_router(table.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())