from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message):
    is_admin = message.from_user.id in ADMIN_IDS
    text = """
🎮 **eFootball TURNIR BOTI** 🤖

Turnirga ro'yxatdan o'tish uchun quyidagi tugmani bosing:
    """
    register_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Turnirga ro'yxatdan o'tish", callback_data="register")]
        ]
    )
    await message.answer(text, reply_markup=register_btn, parse_mode="Markdown")
    if is_admin:
        from handlers.admin import admin_keyboard
        await message.answer("👑 Admin panel:", reply_markup=admin_keyboard())

@router.message(Command("about"))
async def about_command(message: types.Message):
    text = """
🤖 **eFootball Turnir Boti** v2.0

🏆 Turnirga ro'yxatdan o'tish: /start
👨‍💻 Developer: @Shukurullo
📅 2026
    """
    await message.answer(text, parse_mode="Markdown")

# =============== TEST TUGMALAR ===============
@router.message(Command("test"))
async def simple_test(message: types.Message):
    await message.answer("✅ Test ishladi!")

@router.callback_query(F.data == "test")
async def simple_callback(callback: types.CallbackQuery):
    await callback.message.answer("✅ Callback ishladi!")
    await callback.answer()