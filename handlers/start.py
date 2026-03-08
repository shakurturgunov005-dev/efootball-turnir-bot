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
