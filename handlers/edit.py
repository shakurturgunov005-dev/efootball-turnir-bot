from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS

router = Router()

@router.message(F.text == "📝 Ro'yxatni tahrirlash")
async def edit_list(message: types.Message):
    """Ro'yxatdan o'tganlarni tahrirlash paneli"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    players = await db.get_all_players(paid_only=False)
    
    if not players:
        await message.answer("📭 Ro'yxat bo'sh.")
        return
    
    for player in players:
        status = "✅" if player['payment_status'] else "⏳"
        text = f"{status} {player['full_name']} | @{player['username']}"
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👁 Ko'rish", callback_data=f"view_{player['user_id']}"),
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pay_{player['user_id']}"),
                    InlineKeyboardButton(text="❌ O'chirish", callback_data=f"del_{player['user_id']}")
                ]
            ]
        )
        
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("view_"))
async def view_player(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("view_", ""))
    player = await db.get_player_by_user_id(user_id)
    
    text = f"""
👤 **{player['full_name']}**
⚽️ eFootball: @{player['username']}
📱 Telegram: @{player['telegram_username']}
🆔 {player['user_id']}
✅ To'lov: {"Qilingan" if player['payment_status'] else "Kutilmoqda"}
📅 Ro'yxat: {player['registered_at'].strftime('%d.%m.%Y %H:%M')}
    """
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("pay_"))
async def confirm_payment_edit(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("pay_", ""))
    await db.update_payment_status(user_id)
    
    await callback.message.edit_text("✅ To'lov tasdiqlandi!")
    await callback.answer()

@router.callback_query(F.data.startswith("del_"))
async def delete_player(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("del_", ""))
    await db.delete_player(user_id)
    
    await callback.message.edit_text("❌ Foydalanuvchi o'chirildi!")
    await callback.answer()