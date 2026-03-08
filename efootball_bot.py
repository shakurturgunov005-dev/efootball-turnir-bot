import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

MAX_PLAYERS = 16

#database.py
import asyncpg
from config import DATABASE_URL

async def connect():
    return await asyncpg.connect(DATABASE_URL)

async def setup():
    conn = await connect()

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS players(
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        name TEXT,
        game_username TEXT,
        tg_username TEXT,
        payment BOOLEAN DEFAULT FALSE
    )
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS matches(
        id SERIAL PRIMARY KEY,
        player1 TEXT,
        player2 TEXT,
        score TEXT,
        winner TEXT,
        round TEXT
    )
    """)

    await conn.close()
    
#utils/brasket.py
import random

def generate_bracket(players):

    random.shuffle(players)

    matches = []

    for i in range(0,16,2):

        matches.append(
            (players[i], players[i+1])
        )

    text = "🏆 1/8 FINAL\n\n"

    for p1,p2 in matches:

        text += f"{p1} 🆚 {p2}\n"

    return matches,text
    
#utils/channel.py
from config import CHANNEL_ID

CHANNEL_POST = None

async def update_channel(bot, players):

    global CHANNEL_POST

    text = "🏆 TURNIR ISHTIROKCHILARI\n\n"

    for i,p in enumerate(players,1):

        text += f"{i}. {p}\n"

    text += f"\n👥 {len(players)}/16"

    if CHANNEL_POST is None:

        msg = await bot.send_message(CHANNEL_ID,text)

        CHANNEL_POST = msg.message_id

    else:

        await bot.edit_message_text(
            text,
            CHANNEL_ID,
            CHANNEL_POST
        )
    
#bot.py
import asyncio
from aiogram import Bot,Dispatcher

from config import BOT_TOKEN
from database import setup

from handlers import start,registration,payment,admin,matches

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(registration.router)
dp.include_router(payment.router)
dp.include_router(admin.router)
dp.include_router(matches.router)

async def main():

    await setup()

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
    
#=============handlers start===============
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("start"))
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🏆 Turnirga yozilish",
                callback_data="join"
            )]
        ]
    )

    await msg.answer(
        "🏆 EFOOTBALL TURNIR\n\n"
        "Ro'yxatdan o'tish uchun tugmani bosing",
        reply_markup=kb
    )
        
#handlers/registration.py


#handlers/payment.py
from aiogram import F,types
from config import ADMIN_ID

def register(dp):

    @dp.message(F.photo)
    async def payment(msg:types.Message):

        photo = msg.photo[-1].file_id

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✅ Tasdiqlash",
                        callback_data=f"ok_{msg.from_user.id}"
                    )
                ]
            ]
        )

        await msg.bot.send_photo(
            ADMIN_ID,
            photo,
            caption=f"To'lov\nUser:{msg.from_user.id}",
            reply_markup=kb
        )

        await msg.answer("⏳ Tekshirilmoqda")
        
#handlers/admin.py
from aiogram import F,types
from database import connect
from config import ADMIN_ID

def register(dp):

    @dp.callback_query(F.data.startswith("ok_"))
    async def approve(call:types.CallbackQuery):

        uid = int(call.data.split("_")[1])

        conn = await connect()

        await conn.execute(
            "UPDATE players SET payment=TRUE WHERE user_id=$1",
            uid
        )

        await call.bot.send_message(
            uid,
            "✅ Turnirga qo'shildingiz"
        )

        await call.answer("Tasdiqlandi")
