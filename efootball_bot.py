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

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 🔴 MUHIM: O'ZINGIZNING MA'LUMOTLARINGIZNI YOZING
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_IDS = [6042457335]      # 👈 SIZNING ID

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
            user_id BIGINT UNIQUE,
            username TEXT,
            full_name TEXT NOT NULL,
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

# ================= COMMAND HANDLERS =================
@dp.message(CommandStart())
async def start_handler(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    text = """
🎮 **eFootball TURNIR BOTI** 🤖

Bu bot orqali turnirga ro'yxatdan o'tishingiz mumkin.

🔹 /register - Turnirga ro'yxatdan o'tish
🔹 /players - Ishtirokchilar ro'yxati
🔹 /about - Bot haqida
"""
    if is_admin:
        await message.answer(text, reply_markup=admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")

@dp.message(Command("register"))
async def register_command(message: Message):
    await register_user(message.from_user, message)

@dp.message(Command("players"))
async def players_command(message: Message):
    await show_players(message)

@dp.message(Command("about"))
async def about_command(message: Message):
    text = """
🎮 **eFootball Turnir Boti** v1.0

🏆 Turnirga ro'yxatdan o'tish uchun /register

👨‍💻 Developer: @Shukurullo
📅 2026
"""
    await message.answer(text, parse_mode="Markdown")

# ================= ADMIN HANDLERS =================
@dp.message(F.text == "📋 Ishtirokchilar")
async def show_players(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tournament_players ORDER BY id")
    
    if not rows:
        await message.answer("📭 Hali hech kim ro'yxatdan o'tmagan.")
        return
    
    text = f"📋 **Turnir ishtirokchilari** ({len(rows)}/{MAX_PLAYERS})\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row['full_name']}\n"
        if row['username'] and row['username'] != "username yo'q":
            text += f"   👤 @{row['username']}\n"
        text += f"   🕐 {row['registered_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if len(text) > 4000:
        for x in range(0, len(text), 4000):
            await message.answer(text[x:x+4000], parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM tournament_players")
        last = await conn.fetchrow("SELECT * FROM tournament_players ORDER BY id DESC LIMIT 1")
    
    text = f"""
━━━━━━━━━━━━━━━━━━
📊 STATISTIKA
━━━━━━━━━━━━━━━━━━

👥 Jami ishtirokchilar: {count}/{MAX_PLAYERS}
🕐 Bo'sh joy: {MAX_PLAYERS - count}

📅 Oxirgi ro'yxatdan o'tgan:
   {last['full_name'] if last else 'Yo\'q'}
   🕐 {last['registered_at'].strftime('%d.%m.%Y %H:%M') if last else ''}
━━━━━━━━━━━━━━━━━━
"""
    await message.answer(f"<pre>{text}</pre>", parse_mode="HTML")

@dp.message(F.text == "📢 Kanalga post yuborish")
async def send_post(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    register_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Turnirga ro'yxatdan o'tish", callback_data="register")]
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

# ================= CALLBACK HANDLERS =================
@dp.callback_query(F.data == "register")
async def register_callback(callback: CallbackQuery):
    result = await register_user(callback.from_user, callback.message)
    await callback.answer()
    
    if result:
        user = callback.from_user
        name = user.full_name
        username = f"@{user.username}" if user.username else "username yo'q"
        count = await get_count()
        
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"""
━━━━━━━━━━━━━━━━━━
✅ YANGI ISHTIROKCHI
━━━━━━━━━━━━━━━━━━

👤 {name}
📱 {username}
👥 Jami: {count}/{MAX_PLAYERS}
━━━━━━━━━━━━━━━━━━
""",
            parse_mode="Markdown"
        )

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

# ================= FUNCTIONS =================
async def register_user(user, message):
    user_id = user.id
    username = user.username or "username yo'q"
    full_name = user.full_name
    
    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM tournament_players")
        
        if count >= MAX_PLAYERS:
            await message.answer("❌ Ro'yxat yakunlandi! Maksimal 16 kishi.")
            return False
        
        try:
            await conn.execute("""
                INSERT INTO tournament_players (user_id, username, full_name)
                VALUES ($1, $2, $3)
            """, user_id, username, full_name)
            
            await message.answer(
                f"""
━━━━━━━━━━━━━━━━━━
✅ TABRIKLAYMIZ!
━━━━━━━━━━━━━━━━━━

Siz turnirga ro'yxatdan o'tdingiz!

👥 Ishtirokchingiz: {count+1}/{MAX_PLAYERS}
📢 Kanal: @your_channel
━━━━━━━━━━━━━━━━━━
""",
                parse_mode="Markdown"
            )
            return True
            
        except:
            await message.answer("❌ Siz avval ro'yxatdan o'tgansiz!")
            return False

async def get_count():
    async with db_pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM tournament_players")

# ================= STARTUP =================
@app.on_event("startup")
async def startup():
    global db_pool
    
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="register", description="Turnirga ro'yxatdan o'tish"),
        BotCommand(command="players", description="Ishtirokchilar ro'yxati"),
        BotCommand(command="about", description="Bot haqida")
    ]
    await bot.set_my_commands(commands)
    
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    await init_db()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    
    print("✅ eFootball Bot ishga tushdi!")

# ================= WEBHOOK =================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return JSONResponse({"ok": True})
    except Exception as e:
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
