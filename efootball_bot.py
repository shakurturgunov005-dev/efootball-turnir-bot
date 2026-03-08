import asyncio
import os
import asyncpg
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, BotCommand
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn
import pytz
import re

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Kanal ID
ADMIN_IDS = [6042457335]  # Admin ID

UZ_TZ = pytz.timezone("Asia/Tashkent")

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)
app = FastAPI()
scheduler = AsyncIOScheduler(timezone=UZ_TZ)

db_pool = None
MAX_PLAYERS = 16  # Maksimal ishtirokchilar

# ================= DATABASE =================
async def init_db():
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS tournament_players (
            id SERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            efootball_username TEXT NOT NULL,
            telegram_username TEXT NOT NULL,
            user_id BIGINT UNIQUE,
            registered_at TIMESTAMP DEFAULT NOW()
        )
        """)

# ================= KEYBOARDS =================
def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ishtirokchilar")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Kanalga post yuborish")],
            [KeyboardButton(text="🗑 Ro'yxatni tozalash")]
        ],
        resize_keyboard=True
    )

# ================= REGISTRATION FORMAT =================
REGISTRATION_TEMPLATE = """
📝 TURNIRGA RO'YXATDAN O'TISH

1️⃣ Ismingiz : 
2️⃣ eFootball username : 
3️⃣ Telegram username : 

📌 To'ldirib, shu joyga qayta yuboring.
"""

# ================= COMMAND HANDLERS =================
@dp.message(CommandStart())
async def start_handler(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    text = """
🎮 **eFootball TURNIR BOTI** 🤖

Turnirga ro'yxatdan o'tish uchun quyidagi tugmani bosing:

👇👇👇
"""
    # Inline tugma
    register_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Turnirga ro'yxatdan o'tish", callback_data="register_start")]
        ]
    )
    
    if is_admin:
        await message.answer(text, reply_markup=register_button, parse_mode="Markdown")
        await message.answer("Admin panel:", reply_markup=admin_keyboard())
    else:
        await message.answer(text, reply_markup=register_button, parse_mode="Markdown")

# ================= CALLBACK HANDLERS =================
@dp.callback_query(F.data == "register_start")
async def register_start(callback: CallbackQuery):
    """Ro'yxatdan o'tishni boshlash"""
    await callback.message.answer(REGISTRATION_TEMPLATE, parse_mode="Markdown")
    await callback.answer()

# ================= REGISTRATION HANDLER =================
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_registration(message: Message):
    """Foydalanuvchi yuborgan ma'lumotlarni qabul qilish"""
    
    # Formatni tekshirish
    text = message.text.strip()
    lines = text.split('\n')
    
    if len(lines) < 3:
        await message.answer("❌ Noto'g'ri format. Iltimos, ko'rsatilgan shablon bo'yicha to'ldiring.")
        return
    
    try:
        # Ma'lumotlarni ajratib olish
        full_name = ""
        efootball_username = ""
        telegram_username = ""
        
        for line in lines:
            if "1️⃣ Ismingiz :" in line:
                full_name = line.replace("1️⃣ Ismingiz :", "").strip()
            elif "2️⃣ eFootball username :" in line:
                efootball_username = line.replace("2️⃣ eFootball username :", "").strip()
            elif "3️⃣ Telegram username :" in line:
                telegram_username = line.replace("3️⃣ Telegram username :", "").strip()
        
        if not full_name or not efootball_username or not telegram_username:
            await message.answer("❌ Barcha maydonlarni to'ldiring!")
            return
        
        # Databasega saqlash
        async with db_pool.acquire() as conn:
            # Avval ro'yxatdan o'tganmi tekshirish
            existing = await conn.fetchval(
                "SELECT user_id FROM tournament_players WHERE user_id = $1",
                message.from_user.id
            )
            
            if existing:
                await message.answer("❌ Siz avval ro'yxatdan o'tgansiz!")
                return
            
            # Saqlash
            await conn.execute("""
                INSERT INTO tournament_players (full_name, efootball_username, telegram_username, user_id)
                VALUES ($1, $2, $3, $4)
            """, full_name, efootball_username, telegram_username, message.from_user.id)
            
            # Nechanchi ishtirokchi ekanligini aniqlash
            count = await conn.fetchval("SELECT COUNT(*) FROM tournament_players")
        
        # Muvaffaqiyatli ro'yxatdan o'tdi
        await message.answer(f"✅ Tabriklaymiz! Siz {count}-ishtirokchi bo'ldingiz!")
        
        # Kanala xabar yuborish (faqat ism va raqam)
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"{count}. {full_name}"
        )
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

# ================= ADMIN HANDLERS =================
@dp.message(F.text == "📋 Ishtirokchilar")
async def show_players(message: Message):
    """Ishtirokchilar ro'yxatini ko'rish"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tournament_players ORDER BY id")
    
    if not rows:
        await message.answer("📭 Hali hech kim ro'yxatdan o'tmagan.")
        return
    
    text = f"📋 **Turnir ishtirokchilari** ({len(rows)}/{MAX_PLAYERS})\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for row in rows:
        text += f"{row['id']}. {row['full_name']}\n"
        text += f"   ⚽ eFootball: @{row['efootball_username']}\n"
        text += f"   📱 Telegram: @{row['telegram_username']}\n"
        text += f"   🕐 {row['registered_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM tournament_players")
    
    text = f"""
━━━━━━━━━━━━━━━━━━
📊 STATISTIKA
━━━━━━━━━━━━━━━━━━

👥 Jami ishtirokchilar: {count}/{MAX_PLAYERS}
🕐 Bo'sh joy: {MAX_PLAYERS - count}
━━━━━━━━━━━━━━━━━━
"""
    await message.answer(f"<pre>{text}</pre>", parse_mode="HTML")

@dp.message(F.text == "📢 Kanalga post yuborish")
async def send_post(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    register_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Turnirga ro'yxatdan o'tish", callback_data="register_start")]
        ]
    )
    
    post_text = """
━━━━━━━━━━━━━━━━━━
🎮 eFootball TURNIRI ⚽️
━━━━━━━━━━━━━━━━━━

🏆 **Sovrin:** 1 000 000 so'm
📅 **Sana:** 2026.03.15
⏰ **Vaqt:** 20:00
👥 **Ishtirokchilar:** 16 kishi
💰 **To'lov:** Bepul

✅ Ro'yxatdan o'tish uchun tugmani bosing!
━━━━━━━━━━━━━━━━━━
"""
    
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=post_text,
        reply_markup=register_button,
        parse_mode="Markdown"
    )
    
    await message.answer("✅ Post kanalga yuborildi!")

@dp.message(F.text == "🗑 Ro'yxatni tozalash")
async def clear_players(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha", callback_data="clear_yes")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data="clear_no")]
        ]
    )
    
    await message.answer("⚠️ Ro'yxatni tozalashni xohlaysizmi?", reply_markup=keyboard)

@dp.callback_query(F.data == "clear_yes")
async def clear_yes(callback: CallbackQuery):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM tournament_players")
    await callback.message.edit_text("✅ Ro'yxat tozalandi!")
    await callback.answer()

@dp.callback_query(F.data == "clear_no")
async def clear_no(callback: CallbackQuery):
    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer()

@dp.message(Command("about"))
async def about_command(message: Message):
    text = """
🎮 **eFootball Turnir Boti** v2.0

🏆 Turnirga ro'yxatdan o'tish:
   /start

👨‍💻 Developer: @Shukurullo
📅 2026
"""
    await message.answer(text, parse_mode="Markdown")

# ================= STARTUP =================
@app.on_event("startup")
async def startup():
    global db_pool
    
    try:
        commands = [
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="about", description="Bot haqida")
        ]
        await bot.set_my_commands(commands)
        
        # Database ulanishi
        print(f"🔄 Database ga ulanish...")
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        await init_db()
        print("✅ Database tayyor!")
        
        # Webhook
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(WEBHOOK_URL)
        print(f"✅ Webhook sozlandi: {WEBHOOK_URL}")
        
        print("✅ eFootball Bot ishga tushdi!")
        
    except Exception as e:
        print(f"❌ XATOLIK: {e}")
        import traceback
        traceback.print_exc()

# ================= WEBHOOK =================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return JSONResponse({"ok": True})
    except Exception as e:
        print(f"Webhook xatolik: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    if db_pool:
        await db_pool.close()

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)