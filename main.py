import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import db

# handlers
from handlers import user
from handlers import registration
from handlers import payment
from handlers import table
from handlers import admin   # ⬅️ SHU QATOR QO'SHILADI

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():

    await db.create_pool()

    dp.include_router(user.router)
    dp.include_router(registration.router)
    dp.include_router(payment.router)
    dp.include_router(table.router)
    dp.include_router(admin.router)   # ⬅️ SHU QATOR QO'SHILADI

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())