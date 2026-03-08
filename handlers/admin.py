from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS, MAX_PLAYERS

router = Router()

# ================= ADMIN KEYBOARD =================
def admin_keyboard():
    """Admin panel uchun klaviatura"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ishtirokchilar")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Post yuborish")],
            [KeyboardButton(text="💰 To'lov tekshirish")],
            [KeyboardButton(text="⚽️ Match yaratish")],
            [KeyboardButton(text="🗑 Tozalash")]
        ],
        resize_keyboard=True
    )

# ================= ISHTIROKCHILAR =================
@router.message(F.text == "📋 Ishtirokchilar")
async def show_players(message: types.Message):
    """Barcha ishtirokchilarni ko'rsatish"""
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    players = await db.get_all_players(paid_only=True)
    
    if not players:
        await message.answer("📭 Hali ishtirokchilar yo'q.")
        return
    
    text = f"📋 **Ishtirokchilar** ({len(players)}/{MAX_PLAYERS})\n\n"
    for p in players:
        text += f"{p['id']}. {p['full_name']} - @{p['username']}\n"
        text += f"   ✅ To'lov qilingan\n\n"
    
    await message.answer(text, parse_mode="Markdown")

# ================= STATISTIKA =================
@router.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    """Statistika ma'lumotlarini ko'rsatish"""
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    total, paid, waiting = await db.get_statistics()
    
    text = f"""
📊 **STATISTIKA**
━━━━━━━━━━━━━━━━━━
👥 Jami ro'yxatdan o'tgan: {total}
✅ To'lov qilgan: {paid}
⏳ Tekshirilmagan: {waiting}
🕐 Bo'sh joy: {MAX_PLAYERS - paid}
━━━━━━━━━━━━━━━━━━
"""
    await message.answer(text, parse_mode="Markdown")

# ================= TO'LOV TEKSHIRISH =================
@router.message(F.text == "💰 To'lov tekshirish")
async def check_payments(message: types.Message):
    """Tekshirilmagan to'lovlarni ko'rsatish"""
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # To'lov qilmagan, lekin chek yuborganlarni olish
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM players WHERE payment_status = FALSE AND payment_photo IS NOT NULL"
        )
    
    if not rows:
        await message.answer("📭 Tekshirilmagan to'lovlar yo'q.")
        return
    
    for row in rows:
        # Tasdiqlash tugmasi bilan xabar yuborish
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="✅ Tasdiqlash", 
                    callback_data=f"confirm_{row['user_id']}"
                )]
            ]
        )
        
        await message.answer(
            f"💰 **Yangi to'lov**\n\n👤 {row['full_name']}\n🆔 {row['user_id']}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Chek rasmini yuborish
        if row['payment_photo']:
            await message.bot.send_photo(
                message.chat.id,
                row['payment_photo'],
                caption="📸 To'lov cheki"
            )

# ================= TO'LOVNI TASDIQLASH =================
@router.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    """To'lovni tasdiqlash"""
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    
    user_id = int(callback.data.replace("confirm_", ""))
    
    # To'lov statusini yangilash
    await db.update_payment_status(user_id)
    
    # Foydalanuvchi ma'lumotlarini olish
    user = await db.get_player_by_user_id(user_id)
    
    # Nechanchi ishtirokchi ekanligini aniqlash
    paid_count = await db.get_all_players(paid_only=True)
    count = len(paid_count)
    
    # Foydalanuvchiga xabar yuborish
    try:
        await callback.bot.send_message(
            user_id,
            f"✅ **Tabriklaymiz!**\n\nTo'lovingiz tasdiqlandi.\nSiz {count}-ishtirokchi bo'ldingiz!",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_text(f"✅ To'lov tasdiqlandi: {user['full_name']}")
    await callback.answer("✅ Tasdiqlandi")

# ================= POST YUBORISH =================
@router.message(F.text == "📢 Post yuborish")
async def send_post(message: types.Message):
    """Kanalga post yuborish"""
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # To'lov qilgan ishtirokchilarni olish
    players = await db.get_all_players(paid_only=True)
    
    if not players:
        await message.answer("📭 Hali ishtirokchilar yo'q.")
        return
    
    # Post matnini tayyorlash
    text = "━━━━━━━━━━━━━━━━━━\n"
    text += "📋 **TURNIR RO'YXATI**\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, player in enumerate(players, 1):
        text += f"{i}. {player['full_name']}\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━"
    
    # Ro'yxatdan o'tish tugmasi
    register_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Turnirga ro'yxatdan o'tish", callback_data="register")]
        ]
    )
    
    from config import CHANNEL_ID
    await message.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        reply_markup=register_btn,
        parse_mode="Markdown"
    )
    
    await message.answer("✅ Post kanalga yuborildi!")

# ================= TOZALASH =================
@router.message(F.text == "🗑 Tozalash")
async def clear_all(message: types.Message):
    """Barcha ma'lumotlarni tozalash (faqat admin)"""
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="clear_yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="clear_no")
            ]
        ]
    )
    
    await message.answer("⚠️ **Barcha ma'lumotlarni tozalashni xohlaysizmi?**", 
                         reply_markup=keyboard, 
                         parse_mode="Markdown")

@router.callback_query(F.data == "clear_yes")
async def clear_yes(callback: types.CallbackQuery):
    """Tozalashni tasdiqlash"""
    
    async with db.pool.acquire() as conn:
        await conn.execute("DELETE FROM players")
        await conn.execute("DELETE FROM matches")
    
    await callback.message.edit_text("✅ Barcha ma'lumotlar tozalandi!")
    await callback.answer()

@router.callback_query(F.data == "clear_no")
async def clear_no(callback: types.CallbackQuery):
    """Tozalashni bekor qilish"""
    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer()
