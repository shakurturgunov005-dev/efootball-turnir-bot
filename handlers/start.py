from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS

router = Router()


# INLINE MENU
def main_menu():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="register")
            ],

            [
                InlineKeyboardButton(text="👥 Ishtirokchilar", callback_data="players"),
                InlineKeyboardButton(text="🏆 Jadval", callback_data="table")
            ],

            [
                InlineKeyboardButton(text="🎮 Matchlar", callback_data="matches"),
                InlineKeyboardButton(text="ℹ️ Turnir haqida", callback_data="about_turnir")
            ]

        ]
    )

    return keyboard


# START
@router.message(CommandStart())
async def start_handler(message: types.Message):

    text = """
🎮 **eFootball TURNIR BOTI** 🤖

🏆 Professional turnirga xush kelibsiz!

Quyidagi menyu orqali turnirda qatnashing.
"""

    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# ABOUT
@router.callback_query(F.data == "about_turnir")
async def about_turnir(callback: types.CallbackQuery):

    text = """
ℹ️ **Turnir haqida**

🎮 O'yin: eFootball  
👥 Format: 16 o'yinchi  
🏆 Sistema: PlayOff  

💰 Turnir badali: **300₽**

To'lov tasdiqlangandan so'ng ishtirokchi ro'yxatga qo'shiladi.
"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

    await callback.answer()


# TEST
@router.message(Command("test"))
async def test_button(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ TEST", callback_data="test")]
        ]
    )

    await message.answer("Test tugmasini bosing:", reply_markup=keyboard)


@router.callback_query(F.data == "test")
async def test_callback(callback: types.CallbackQuery):

    await callback.message.answer("✅ Test ishladi!")
    await callback.answer()