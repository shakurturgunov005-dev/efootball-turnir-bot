import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_IDS
from database import db
from utils.channel import init_channel_post
from handlers import edit  # 🔥 YANGI

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

# ================= BOTNI ISHGA TUSHIRISH =================
async def main():
    """Asosiy funksiya"""
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
        
        # Botni polling rejimida ishga tushirish
        logger.info("✅ Bot ishga tushdi!")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        raise
    finally:
        # Databaseni yopish
        await db.close()
        logger.info("👋 Bot to'xtatildi")

# ================= ISHGA TUSHIRISH =================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Kutilmagan xatolik: {e}")
