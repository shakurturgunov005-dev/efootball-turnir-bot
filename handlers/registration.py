from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db

router = Router()

REGISTRATION_TEMPLATE = """
📝 **TURNIRGA RO'YXATDAN O'TISH**

1️⃣ Ismingiz : 
2️⃣ eFootball username : 
3️⃣ Telegram username : 

📌 To'ldirib, shu botga qayta yuboring.
"""

@router.callback_query(F.data == "register")
async def register_start(callback: types.CallbackQuery):
    """Ro'yxatdan o'tishni boshlash"""
    await callback.message.answer(REGISTRATION_TEMPLATE, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text & ~F.text.startswith("/") & ~F.photo)
async def handle_registration(message: types.Message):
    """Foydalanuvchi yuborgan ma'lumotlarni qabul qilish"""
    
    text = message.text.strip()
    lines = text.split('\n')
    
    if len(lines) < 3:
        await message.answer("❌ Noto'g'ri format. Iltimos, ko'rsatilgan shablon bo'yicha to'ldiring.")
        return
    
    try:
        full_name = ""
        username = ""
        telegram_username = ""
        
        for line in lines:
            if "1️⃣" in line and ":" in line:
                full_name = line.split(":", 1)[-1].strip()
            elif "2️⃣" in line and ":" in line:
                username = line.split(":", 1)[-1].strip()
            elif "3️⃣" in line and ":" in line:
                telegram_username = line.split(":", 1)[-1].strip()
        
        if not full_name or not username or not telegram_username:
            await message.answer("❌ Barcha maydonlarni to'ldiring!")
            return
        
        # Avval ro'yxatdan o'tganmi tekshirish
        existing = await db.get_player_by_user_id(message.from_user.id)
        if existing:
            await message.answer("❌ Siz avval ro'yxatdan o'tgansiz!")
            return
        
        # Yangi ishtirokchini qo'shish
        await db.add_player(full_name, username, telegram_username, message.from_user.id)
        
        # To'lovni tasdiqlash tugmalari
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ HA, o'zim xohlayman", callback_data="confirm_yes"),
                    InlineKeyboardButton(text="❌ YO'Q", callback_data="confirm_no")
                ]
            ]
        )
        
        await message.answer(
            "⚠️ To'lovni o'zingiz xohlab qilyapsizmi?\nHech kim majburlamayaptimi?",
            reply_markup=confirm_keyboard
        )
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
