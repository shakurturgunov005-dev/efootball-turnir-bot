from aiogram import Router, types
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