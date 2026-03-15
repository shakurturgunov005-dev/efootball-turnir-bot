from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from config import ADMIN_IDS, MAX_PLAYERS

router = Router()


def main_menu(user_id, players_count):

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"📝 Ro'yxatdan o'tish ({players_count}/{MAX_PLAYERS})",
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

    # ADMIN TEKSHIRISH (TO'G'RI VARIANT)
    if int(user_id) in ADMIN_IDS:

        keyboard.append([
            InlineKeyboardButton(
                text="⏳ Tasdiqlanishi kutilayotganlar",
                callback_data="pending_payments"
            )
        ])

        keyboard.append([
            InlineKeyboardButton(
                text="👥 Ishtirokchilarni boshqarish",
                callback_data="admin_players"
            )
        ])

        keyboard.append([
            InlineKeyboardButton(
                text="📊 Statistika",
                callback_data="admin_stats"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(CommandStart())
async def start(message: types.Message):

    await message.answer(
        f"""
USER ID: {message.from_user.id}
ADMIN IDS: {ADMIN_IDS}
IS ADMIN: {message.from_user.id in ADMIN_IDS}
"""
    )

    players = await db.get_all_players(paid_only=True)
    players_count = len(players)

    text = """
🎮 eFootball TURNIR BOTI

🏆 Professional turnirga xush kelibsiz!
"""

    await message.answer(
        text,
        reply_markup=main_menu(
            message.from_user.id,
            players_count
        )
    )


# ================= /players komandasi =================

@router.message(F.text == "/players")
async def show_players(message: types.Message):

    players = await db.get_all_players(paid_only=True)

    if not players:
        await message.answer("📋 Hozircha tasdiqlangan ishtirokchilar yo'q.")
        return

    text = "🏆 TURNIR ISHTIROKCHILARI\n\n"

    for i, player in enumerate(players, start=1):
        text += f"{i}. {player['full_name']}\n"

    text += f"\n📊 Jami: {len(players)}/16"

    await message.answer(text)


# ================= TUGMA ORQALI ISHTIROKCHILAR =================

@router.callback_query(F.data == "players")
async def players_button(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if not players:
        await callback.message.answer("📋 Hozircha tasdiqlangan ishtirokchilar yo'q.")
        await callback.answer()
        return

    text = "🏆 TURNIR ISHTIROKCHILARI\n\n"

    for i, player in enumerate(players, start=1):
        text += f"{i}. {player['full_name']}\n"

    text += f"\n📊 Jami: {len(players)}/16"

    await callback.message.answer(text)

    await callback.answer()