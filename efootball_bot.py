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

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_IDS = [6042457335]

UZ_TZ = pytz.timezone("Asia/Tashkent")

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)
app = FastAPI()
scheduler = AsyncIOScheduler(timezone=UZ_TZ)

db_pool = None
MAX_PLAYERS = 16

# 💰 TO'LOV MA'LUMOTLARI
CARD_NUMBER = "1234 5678 9012 3456"  # 👈 O'Z KARTANGIZ
CARD_HOLDER = "SHUKURULLO TURGUNOV"  # 👈 KARTADAGI ISM
PAYMENT_AMOUNT = 300  # 300 rubl

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
            payment_status BOOLEAN DEFAULT FALSE,
            payment_photo TEXT,
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
            [KeyboardButton(text="💰 To'lovni tekshirish")],
            [KeyboardButton(text="✅ To'lovni tasdiqlash")],
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
@dp.message(F.text & ~F.text.startswith("/") & ~F.photo)
async def handle_registration(message: Message):
    """Foydalanuvchi yuborgan ma'lumotlarni qabul qilish"""
    
    text = message.text.strip()
    lines = text.split('\n')
    
    if len(lines) < 3:
        await message.answer("❌ Noto'g'ri format. Iltimos, ko'rsatilgan shablon bo'yicha to'ldiring.")
        return
    
    try:
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
        
        # Databasega vaqtincha saqlash (to'lov qilinmagan)
        async with db_pool.acquire() as conn:
            existing = await conn.fetchval(
                "SELECT user_id FROM tournament_players WHERE user_id = $1",
                message.from_user.id
            )
            
            if existing:
                await message.answer("❌ Siz avval ro'yxatdan o'tgansiz!")
                return
            
            await conn.execute("""
                INSERT INTO tournament_players (full_name, efootball_username, telegram_username, user_id, payment_status)
                VALUES ($1, $2, $3, $4, $5)
            """, full_name, efootball_username, telegram_username, message.from_user.id, False)
        
        # So'rov yuborish (✅ HA / ❌ YO'Q tugmalari bilan)
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ HA, o'zim xohlayman", callback_data="confirm_yes"),
                    InlineKeyboardButton(text="❌ YO'Q", callback_data="confirm_no")
                ]
            ]
        )
        
        confirm_msg = await message.answer(
            "⚠️ To'lovni o'zingiz xohlab qilyapsizmi?\nHech kim majburlamayaptimi?",
            reply_markup=confirm_keyboard
        )
        
        # Foydalanuvchi ID sini callback_data uchun saqlash
        await confirm_msg.edit_text(
            confirm_msg.text,
            reply_markup=confirm_keyboard
        )
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

# ================= CONFIRMATION HANDLERS =================
@dp.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery):
    """Foydalanuvchi HA ni bosdi"""
    
    # So'rov xabarini o'chirish
    await callback.message.delete()
    
    # To'lov ma'lumotlarini yuborish
    payment_text = f"""
💳 **TO'LOV MA'LUMOTLARI**

Turnirda ishtirok etish uchun {PAYMENT_AMOUNT} ₽ to'lashingiz kerak.

**Karta raqami:** `{CARD_NUMBER}`
**Qabul qiluvchi:** {CARD_HOLDER}

📌 To'lovni amalga oshirgach, **chekni (skrinshot)** shu yerga yuboring.

Admin to'lovni tasdiqlagach, ro'yxatdan o'tgan hisoblanasiz.
"""
    await callback.message.answer(payment_text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "confirm_no")
async def confirm_no(callback: CallbackQuery):
    """Foydalanuvchi YO'Q ni bosdi"""
    
    # So'rov xabarini o'chirish
    await callback.message.delete()
    
    # Bekor qilish xabarini yuborish va o'chirish
    cancel_msg = await callback.message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")
    
    # 5 sekunddan keyin xabarni o'chirish
    await asyncio.sleep(5)
    await cancel_msg.delete()
    
    # Foydalanuvchi ma'lumotlarini database'dan o'chirish (agar kerak bo'lsa)
    async with db_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM tournament_players WHERE user_id = $1 AND payment_status = FALSE",
            callback.from_user.id
        )
    
    await callback.answer()

# ================= PAYMENT HANDLER =================
@dp.message(F.photo)
async def handle_payment_photo(message: Message):
    """To'lov chekini qabul qilish"""
    
    user_id = message.from_user.id
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM tournament_players WHERE user_id = $1",
            user_id
        )
        
        if not user:
            await message.answer("❌ Avval ro'yxatdan o'ting!")
            return
        
        if user['payment_status']:
            await message.answer("✅ Sizning to'lovingiz allaqachon tasdiqlangan!")
            return
        
        photo_id = message.photo[-1].file_id
        await conn.execute(
            "UPDATE tournament_players SET payment_photo = $1 WHERE user_id = $2",
            photo_id, user_id
        )
    
    await message.answer("✅ To'lov cheki qabul qilindi. Admin tekshirgach, ro'yxatdan o'tasiz.")
    
    # Adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"💰 **Yangi to'lov keldi!**\n\n👤 {user['full_name']}\n🆔 {user_id}\n\nChekni tekshirish uchun pastdagi tugmani bosing:",
                parse_mode="Markdown"
            )
            await bot.send_photo(admin_id, photo_id)
        except:
            pass

# ================= ADMIN PAYMENT HANDLERS =================
@dp.message(F.text == "💰 To'lovni tekshirish")
async def check_payments(message: Message):
    """To'lov qilganlarni ko'rish"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tournament_players WHERE payment_status = FALSE AND payment_photo IS NOT NULL"
        )
    
    if not rows:
        await message.answer("📭 Tekshirilmagan to'lovlar yo'q.")
        return
    
    text = "💰 **Tekshirilmagan to'lovlar:**\n\n"
    
    for row in rows:
        text += f"👤 {row['full_name']}\n"
        text += f"🆔 {row['user_id']}\n"
        text += f"📅 {row['registered_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"➡️ /confirm_{row['user_id']} - tasdiqlash\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.startswith("/confirm_"))
async def confirm_payment(message: Message):
    """To'lovni tasdiqlash"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        user_id = int(message.text.replace("/confirm_", ""))
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE tournament_players SET payment_status = TRUE WHERE user_id = $1",
                user_id
            )
            
            user = await conn.fetchrow(
                "SELECT * FROM tournament_players WHERE user_id = $1",
                user_id
            )
            
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM tournament_players WHERE payment_status = TRUE"
            )
        
        # Foydalanuvchiga xabar
        try:
            await bot.send_message(
                user_id,
                f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi.\nSiz {count}-ishtirokchi bo'ldingiz!"
            )
        except:
            pass
        
        # Kanala xabar
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"{count}. {user['full_name']}"
        )
        
        await message.answer(f"✅ To'lov tasdiqlandi! {user['full_name']} {count}-ishtirokchi.")
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")

@dp.message(F.text == "✅ To'lovni tasdiqlash")
async def confirm_payment_button(message: Message):
    """To'lovni tasdiqlash uchun qo'llanma"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    text = """
✅ **To'lovni tasdiqlash:**

1. /check_payments - tekshirilmagan to'lovlarni ko'ring
2. Har bir foydalanuvchi yonidagi `/confirm_123456` ni bosing

Yoki qo'lda:
/confirm_123456 - (123456 o'rniga user_id yozing)
"""
    await message.answer(text, parse_mode="Markdown")

# ================= ADMIN HANDLERS =================
@dp.message(F.text == "📋 Ishtirokchilar")
async def show_players(message: Message):
    """Ishtirokchilar ro'yxatini ko'rish"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tournament_players WHERE payment_status = TRUE ORDER BY id"
        )
    
    if not rows:
        await message.answer("📭 Hali hech kim ro'yxatdan o'tmagan.")
        return
    
    text = f"📋 **Turnir ishtirokchilari** ({len(rows)}/{MAX_PLAYERS})\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for row in rows:
        text += f"{row['id']}. {row['full_name']}\n"
        text += f"   ⚽ eFootball: @{row['efootball_username']}\n"
        text += f"   📱 Telegram: @{row['telegram_username']}\n"
        text += f"   ✅ To'lov: tasdiqlangan\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with db_pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM tournament_players")
        paid = await conn.fetchval("SELECT COUNT(*) FROM tournament_players WHERE payment_status = TRUE")
        waiting = await conn.fetchval("SELECT COUNT(*) FROM tournament_players WHERE payment_status = FALSE AND payment_photo IS NOT NULL")
    
    text = f"""
━━━━━━━━━━━━━━━━━━
📊 STATISTIKA
━━━━━━━━━━━━━━━━━━

👥 Jami ro'yxatdan o'tgan: {total}
✅ To'lov qilgan: {paid}
⏳ Tekshirilmagan: {waiting}
🕐 Bo'sh joy: {MAX_PLAYERS - paid}
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
    
    post_text = f"""
━━━━━━━━━━━━━━━━━━
🎮 eFootball TURNIRI ⚽️
━━━━━━━━━━━━━━━━━━

🏆 **Sovrin:** Kamida 11ta sovrindor.
📅 **Sana:** 2026.03.10
⏰ **Vaqt:** 20:00
👥 **Ishtirokchilar:** 16 kishi
💰 **To'lov:** {300} ₽
💳 **Karta:** {2202 2063 4229 7533}

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
        
        print(f"🔄 Database ga ulanish...")
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        await init_db()
        print("✅ Database tayyor!")
        
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