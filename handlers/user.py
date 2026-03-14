from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db

router = Router()


def main_menu():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="register"),
                InlineKeyboardButton(text="👥 Ishtirokchilar", callback_data="players")
            ],

            [
                InlineKeyboardButton(text="🏆 Turnir bracket", callback_data="bracket"),
                InlineKeyboardButton(text="📊 Statistika", callback_data="stats")
            ],

            [
                InlineKeyboardButton(text="ℹ️ Turnir haqida", callback_data="info")
            ]

        ]
    )

    return keyboard


@router.message(Command("start"))
async def start(message: types.Message):

    text = """
🎮 eFootball TURNIR BOTI 🤖

🏆 Professional eFootball turniriga xush kelibsiz!

Quyidagi menyudan foydalaning 👇
"""

    await message.answer(
        text,
        reply_markup=main_menu()
    )


# ================= PLAYERS =================

@router.callback_query(F.data == "players")
async def players(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if not players:

        text = "❌ Hali tasdiqlangan ishtirokchilar yo'q."

        await callback.message.edit_text(
            text,
            reply_markup=main_menu()
        )

        return

    text = "👥 ISHTIROKCHILAR\n\n"

    for i, p in enumerate(players, 1):

        tg = f"https://t.me/{p['telegram_username']}"

        text += f"""
№ {i}

1️⃣ Ismi: {p['full_name']}
2️⃣ eFootball username: {p['username']}
3️⃣ Telegram: {tg}

"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )

    await callback.answer()