from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS, MAX_PLAYERS

router = Router()


def main_menu(user_id):

    keyboard = [
        [
            InlineKeyboardButton(
                text="📝 Ro'yxatdan o'tish",
                callback_data="register"
            )
        ],

        [
            InlineKeyboardButton(
                text="👥 Ishtirokchilar",
                callback_data="players"
            ),
            InlineKeyboardButton(
                text="🏆 Jadval",
                callback_data="table"
            )
        ],

        [
            InlineKeyboardButton(
                text="🎮 Matchlar",
                callback_data="matches"
            )
        ],

        [
            InlineKeyboardButton(
                text="ℹ️ Turnir haqida",
                callback_data="about"
            )
        ]
    ]

    if user_id in ADMIN_IDS:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text="👑 Admin panel",
                    callback_data="admin_panel"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(CommandStart())
async def start(message: types.Message):

    players = await db.get_all_players(paid_only=True)

    text = f"""
🎮 eFootball TURNIR BOTI

🏆 Professional turnirga xush kelibsiz!
"""

    await message.answer(
        text,
        reply_markup=main_menu(message.from_user.id)
    )