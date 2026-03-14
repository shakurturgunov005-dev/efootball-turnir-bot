from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database import db

router = Router()


# ================= ADMIN MENU =================

def admin_menu():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💰 To'lovlarni tasdiqlash",
                    callback_data="pending_payments"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Ishtirokchilar",
                    callback_data="admin_players"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data="admin_stats"
                )
            ],
            
            [
                InlineKeyboardButton(
                    text="🧹 Turnirni tozalash",
                    callback_data="clear_tournament"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back"
                )
            ]

        ]
    )

    return keyboard


# ================= OPEN ADMIN PANEL =================

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Siz admin emassiz", show_alert=True)
        return

    text = """
👑 ADMIN PANEL

Kerakli bo'limni tanlang.
"""

    await callback.message.edit_text(
        text,
        reply_markup=admin_menu()
    )

    await callback.answer()


# ================= PLAYERS LIST =================

@router.callback_query(F.data == "admin_players")
async def admin_players(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Siz admin emassiz", show_alert=True)
        return

    players = await db.get_all_players()

    if not players:
        text = "Hali o'yinchilar yo'q."
    else:

        text = "👥 Barcha ishtirokchilar\n\n"

        for i, p in enumerate(players, 1):

            text += (
                f"{i}. {p['full_name']}\n"
                f"🎮 {p['username']}\n"
                f"💰 Paid: {p['payment_status']}\n\n"
            )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel")]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()

# ================= STATS =================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players()
    paid = await db.get_all_players(paid_only=True)

    text = f"""
📊 STATISTIKA

👥 Barcha ro'yxatdan o'tganlar: {len(players)}

💰 To'lov qilganlar: {len(paid)}

⌛ To'lov qilmaganlar: {len(players) - len(paid)}
"""

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel")]
            ]
        )
    )

    await callback.answer()