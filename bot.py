import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from config import BOT_TOKEN
from database import db
from utils.channel import init_channel_post
from handlers import start, registration, payment, matches, admin, edit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

async def include_routers():
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(payment.router)
    dp.include_router(matches.router)
    dp.include_router(admin.router)
    dp.include_router(edit.router)
    logger.info("✅ Barcha routerlar ulandi")

async def set_commands():
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="bracket", description="Turnir jadvali"),
        BotCommand(command="matches", description="Matchlar ro'yxati"),
        BotCommand(command="score", description="Match natijasini kiritish (admin)"),
        BotCommand(command="about", description="Bot haqida")
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Komandalar o'rnatildi")

@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Bot ishga tushmoqda...")
    try:
        await include_routers()
        logger.info("🔄 Database ga ulanish...")
        await db.create_pool()
        logger.info("✅ Database tayyor!")
        init_channel_post(bot)
        logger.info("✅ Kanal post tayyor!")
        await set_commands()
        logger.info("✅ Bot ishga tushdi!")
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    await db.close()
    logger.info("👋 Bot to'xtatildi")

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return JSONResponse({"ok": True})
    except Exception as e:
        logger.error(f"Webhook xatolik: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)