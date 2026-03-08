from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message):
    """Botni ishga tushirish va asosiy menyu"""
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
    
    # Admin bo'lsa, admin panelni ham ko'rsatish
    if is_admin:
        from handlers.admin import admin_keyboard
        await message.answer(
            "👑 Admin panel:", 
            reply_markup=admin_keyboard()
        )

@router.message(Command("about"))
async def about_command(message: types.Message):
    text = """
🤖 **eFootball Turnir Boti** 

🏆 Turnirga ro'yxatdan o'tish: /start
👨‍💻 Developer: SHUKURULLO
📅 2026
⚙️ Version 2.0
    """
    await message.answer(text, parse_mode="Markdown")
    
# ================= TEST TUGMA (vaqtinchalik) =================
@router.message(Command("test"))
async def test_button(message: types.Message):
    """Test tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔴 TEST TUGMA", callback_data="test")]
        ]
    )
    await message.answer("Test tugmasini bosing:", reply_markup=keyboard)

@router.callback_query(F.data == "test")
async def test_callback(callback: types.CallbackQuery):
    """Test tugma bosilganda"""
    await callback.message.answer("✅ Test tugma ishladi!")
    await callback.answer()