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
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel")]
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

    text = "👥 Barcha ishtirokchilar\n\n"
    keyboard = []

    for i, p in enumerate(players, 1):

        text += (
            f"{i}. {p['full_name']}\n"
            f"🎮 {p['username']}\n"
            f"💰 Paid: {p['payment_status']}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {p['full_name']} ni o'chirish",
                callback_data=f"delete_player_{p['user_id']}"
            )
        ])

    keyboard.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel")]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await callback.answer()


# ================= DELETE PLAYER =================

@router.callback_query(F.data.startswith("delete_player_"))
async def delete_player(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Siz admin emassiz", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])

    await db.delete_player(user_id)

    await callback.answer("❌ O'yinchi o'chirildi")

    await callback.message.edit_text(
        "❌ Ishtirokchi o'chirildi",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_players")]
            ]
        )
    )


# ================= CLEAR TOURNAMENT =================

@router.callback_query(F.data == "clear_tournament")
async def clear_tournament(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Siz admin emassiz", show_alert=True)
        return

    await db.delete_all_players()

    await callback.message.edit_text(
        """
🧹 TURNIR TOZALANDI

Barcha ishtirokchilar o'chirildi.
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel")]
            ]
        )
    )

    await callback.answer("Turnir tozalandi")


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