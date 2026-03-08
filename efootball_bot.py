import asyncio
import os
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = 123456789  # admin id
CHANNEL_ID = -1001234567890  # kanal id

bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# DATABASE
async def connect_db():
    return await asyncpg.connect(DATABASE_URL)

async def create_table():
    conn = await connect_db()
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        full_name TEXT,
        game_username TEXT,
        tg_username TEXT,
        payment BOOLEAN DEFAULT FALSE
    )
    """)
    await conn.close()

# START
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Turnirga yozilish", callback_data="join")]
        ]
    )

    await message.answer(
        "🏆 <b>eFootball TURNIR</b>\n\n"
        "Ishtirok etish uchun tugmani bosing.",
        reply_markup=kb
    )

# JOIN
@dp.callback_query(F.data == "join")
async def join(call: types.CallbackQuery):

    conn = await connect_db()

    count = await conn.fetchval("SELECT COUNT(*) FROM players WHERE payment=TRUE")

    if count >= 16:
        await call.message.answer("❌ Turnir to'lgan")
        return

    await call.message.answer(
        "📝 Ro'yxatdan o'tish\n\n"
        "Quyidagi formatda yuboring:\n\n"
        "Ism:\n"
        "Game username:\n"
        "Telegram username:"
    )

# REGISTRATION
@dp.message()
async def register(message: types.Message):

    if message.photo:
        return

    text = message.text.split("\n")

    if len(text) < 3:
        return

    name = text[0]
    game = text[1]
    tg = text[2]

    conn = await connect_db()

    await conn.execute(
        """
        INSERT INTO players(user_id, full_name, game_username, tg_username)
        VALUES($1,$2,$3,$4)
        """,
        message.from_user.id,
        name,
        game,
        tg
    )

    await message.answer(
        "💳 Turnir badali: 300₽\n\n"
        "Karta:\n"
        "2202 2063 4229 7533\n\n"
        "To'lov qilgach screenshot yuboring."
    )

# PAYMENT SCREENSHOT
@dp.message(F.photo)
async def payment(message: types.Message):

    photo = message.photo[-1].file_id

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"ok_{message.from_user.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Bekor",
                    callback_data=f"no_{message.from_user.id}"
                )
            ]
        ]
    )

    await bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"💰 To'lov\n\nUser: {message.from_user.id}",
        reply_markup=kb
    )

    await message.answer("⏳ To'lov tekshirilmoqda")

# ADMIN APPROVE
@dp.callback_query(F.data.startswith("ok_"))
async def approve(call: types.CallbackQuery):

    user_id = int(call.data.split("_")[1])

    conn = await connect_db()

    await conn.execute(
        "UPDATE players SET payment=TRUE WHERE user_id=$1",
        user_id
    )

    await bot.send_message(
        user_id,
        "✅ To'lov tasdiqlandi. Turnirga qo'shildingiz!"
    )

    players = await conn.fetch(
        "SELECT full_name FROM players WHERE payment=TRUE"
    )

    text = "🏆 <b>TURNIR ISHTIROKCHILARI</b>\n\n"

    for i,p in enumerate(players,1):
        text += f"{i}. {p['full_name']}\n"

    text += f"\n👥 {len(players)}/16"

    await bot.send_message(CHANNEL_ID, text)

    await call.answer("Tasdiqlandi")

# ADMIN REJECT
@dp.callback_query(F.data.startswith("no_"))
async def reject(call: types.CallbackQuery):

    user_id = int(call.data.split("_")[1])

    await bot.send_message(
        user_id,
        "❌ To'lov qabul qilinmadi."
    )

    await call.answer("Bekor qilindi")

async def main():
    await create_table()
    await dp.start_polling(bot)

asyncio.run(main())