import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from config import BOT_TOKEN, ADMIN_IDS
from database import db
from utils.channel import init_channel_post
from handlers import edit

# Handlerlarni import qilish
from handlers import (
    start,
    registration,
    payment,
    matches,
    admin
)

# Loggerni sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ================= ROUTERLARNI ULASH =================
async def include_routers():
    """Barcha routerlarni dispatcherga ulash"""
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(payment.router)
    dp.include_router(matches.router)
    dp.include_router(admin.router)
    dp.include_router(edit.router)
    logger.info("✅ Barcha routerlar ulandi")

# ================= BUYRUQLARNI O'RNATISH =================
async def set_commands():
    """Bot komandalarini o'rnatish"""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="bracket", description="Turnir jadvali"),
        BotCommand(command="matches", description="Matchlar ro'yxati"),
        BotCommand(command="score", description="Match natijasini kiritish (admin)"),
        BotCommand(command="about", description="Bot haqida")
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Komandalar o'rnatildi")

# ================= FASTAPI EVENTLARI =================
@app.on_event("startup")
async def on_startup():
    """Bot ishga tushganda"""
    logger.info("🚀 Bot ishga tushmoqda...")
    
    try:
        # Routers
        await include_routers()
        
        # Databaseni ishga tushirish
        logger.info("🔄 Database ga ulanish...")
        await db.create_pool()
        logger.info("✅ Database tayyor!")
        
        # Kanal post obyektini yaratish
        init_channel_post(bot)
        logger.info("✅ Kanal post tayyor!")
        
        # Komandalar
        await set_commands()
        
        logger.info("✅ Bot ishga tushdi!")
        
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    """Bot to'xtaganda"""
    await db.close()
    logger.info("👋 Bot to'xtatildi")

# ================= WEBHOOK =================
@app.post("/webhook")
async def webhook(request: Request):
    """Telegram webhook so'rovlarini qabul qilish"""
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return JSONResponse({"ok": True})
    except Exception as e:
        logger.error(f"Webhook xatolik: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ================= ISHGA TUSHIRISH =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
     
# =============== SODDA TEST ===============
@router.message(Command("test"))
async def simple_test(message: types.Message):
    await message.answer("✅ Test ishladi!")

@router.callback_query(F.data == "test")
async def simple_callback(callback: types.CallbackQuery):
    await callback.message.answer("✅ Callback ishladi!")
    await callback.answer()