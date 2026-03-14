from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import MAX_PLAYERS

router = Router()


# ================= MAIN MENU =================

async def main_menu():

    players = await db.get_all_players()
    count = len(players)

    # turnir to'lgan bo'lsa
    if count >= MAX_PLAYERS:
        register_button = InlineKeyboardButton(
            text=f"❌ Turnir to'ldi ({count}/{MAX_PLAYERS})",
            callback_data="tournament_full"
        )
    else:
        register_button = InlineKeyboardButton(
            text=f"📝 Ro'yxatdan o'tish ({count}/{MAX_PLAYERS})",
            callback_data="register"
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [register_button],
            [
                InlineKeyboardButton(text="👥 Ishtirokchilar", callback_data="players"),
                InlineKeyboardButton(text="🏆 Jadval", callback_data="table")
            ],
            [
                InlineKeyboardButton(text="🎮 Matchlar", callback_data="matches")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Turnir haqida", callback_data="about")
            ]
        ]
    )


# ================= EXIT BUTTON =================

def exit_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Exit", callback_data="back")]
        ]
    )


# ================= START =================

@router.message(CommandStart())
async def start_handler(message: types.Message):

    text = """
🎮 **eFootball TURNIR BOTI** 🤖

🏆 Professional turnirga xush kelibsiz!

Quyidagi menyudan foydalaning.
"""

    await message.answer(
        text,
        reply_markup=await main_menu(),
        parse_mode="Markdown"
    )


# ================= ABOUT =================

@router.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):

    text = """
ℹ️ **Turnir haqida**

🎮 O'yin: eFootball  
👥 Ishtirokchilar: 16  
🏆 Format: Guruh bosqichi + Play-Off  
💰 Badal: 300₽
"""

    await callback.message.edit_text(
        text,
        reply_markup=exit_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= PLAYERS =================

@router.callback_query(F.data == "players")
async def players(callback: types.CallbackQuery):

    players = await db.get_all_players()

    if not players:
        text = "👥 Hali ishtirokchilar yo'q."
    else:
        text = "👥 **Ishtirokchilar ro'yxati**\n\n"

        for i, p in enumerate(players, 1):
            username = f"@{p['username']}" if p['username'] else "username yo'q"
            text += f"{i}. {p['full_name']} - {username}\n"

    await callback.message.edit_text(
        text,
        reply_markup=exit_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= TABLE =================

@router.callback_query(F.data == "table")
async def table(callback: types.CallbackQuery):

    text = """
🏆 **Turnir jadvali**

Jadval hali shakllanmagan.
"""

    await callback.message.edit_text(
        text,
        reply_markup=exit_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= MATCHES =================

@router.callback_query(F.data == "matches")
async def matches(callback: types.CallbackQuery):

    text = """
🎮 **Matchlar**

Matchlar tez orada e'lon qilinadi.
"""

    await callback.message.edit_text(
        text,
        reply_markup=exit_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= TOURNAMENT FULL =================

@router.callback_query(F.data == "tournament_full")
async def tournament_full(callback: types.CallbackQuery):

    await callback.answer(
        "❌ Turnir allaqachon to'lgan!",
        show_alert=True
    )


# ================= EXIT =================

@router.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):

    text = """
🎮 **eFootball TURNIR BOTI** 🤖

🏆 Professional turnirga xush kelibsiz!
"""

    await callback.message.edit_text(
        text,
        reply_markup=await main_menu(),
        parse_mode="Markdown"
    )

    await callback.answer()