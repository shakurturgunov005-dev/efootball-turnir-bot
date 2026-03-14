from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


# ================= MAIN MENU =================

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="register")
            ],
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


# ================= BACK BUTTON =================

def back_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Exit", callback_data="back")]
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
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ================= ABOUT =================

@router.callback_query(F.data == "about")
async def about(callback: types.CallbackQuery):

    text = """
ℹ️ **Turnir haqida**

🎮 O'yin: eFootball  
👥 Ishtirokchilar: 16  
🏆 Format: PlayOff  
💰 Badal: 300₽
"""

    await callback.message.edit_text(
        text,
        reply_markup=back_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= PLAYERS =================

@router.callback_query(F.data == "players")
async def players(callback: types.CallbackQuery):

    text = """
👥 **Ishtirokchilar ro'yxati**

Hozircha ro'yxat shakllanmoqda.
"""

    await callback.message.edit_text(
        text,
        reply_markup=back_button(),
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
        reply_markup=back_button(),
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
        reply_markup=back_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= REGISTER =================

@router.callback_query(F.data == "register")
async def register(callback: types.CallbackQuery):

    text = """
📝 **Turnirga ro'yxatdan o'tish**

Ro'yxatdan o'tish uchun admin bilan bog'laning.
"""

    await callback.message.edit_text(
        text,
        reply_markup=back_button(),
        parse_mode="Markdown"
    )

    await callback.answer()


# ================= BACK =================

@router.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):

    text = """
🎮 **eFootball TURNIR BOTI** 🤖

🏆 Professional turnirga xush kelibsiz!
"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

    await callback.answer()