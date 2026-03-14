from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS

router = Router()


# ================= ADMIN MENU =================

def admin_menu():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⏳ Tasdiqlanishi kutilayotganlar",
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
            ]

        ]
    )

    return keyboard


# ================= ADMIN PANEL =================

@router.message(Command("admin"))
async def admin_panel(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "👑 ADMIN PANEL",
        reply_markup=admin_menu()
    )


# ================= PENDING PAYMENTS =================

@router.callback_query(F.data == "pending_payments")
async def pending_payments(callback: types.CallbackQuery):

    players = await db.get_all_players()

    waiting = []

    for p in players:
        if not p["payment_status"] and p["payment_photo"]:
            waiting.append(p)

    if not waiting:

        await callback.message.edit_text(
            "❌ Tasdiqlanishi kutilayotgan to'lovlar yo'q.",
            reply_markup=admin_menu()
        )

        await callback.answer()
        return

    for p in waiting:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash",
                        callback_data=f"approve_{p['user_id']}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Rad etish",
                        callback_data=f"reject_{p['user_id']}"
                    )
                ]
            ]
        )

        await callback.message.answer_photo(
            p["payment_photo"],
            caption=f"""
💰 To'lov tekshirish

👤 {p['full_name']}
🆔 {p['user_id']}
""",
            reply_markup=keyboard
        )

    await callback.answer()


# ================= APPROVE PAYMENT =================

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await db.update_payment_status(user_id)

    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ To'lov tasdiqlandi"
    )

    await callback.bot.send_message(
        user_id,
        "🎉 To'lovingiz tasdiqlandi! Siz turnirga qo'shildingiz."
    )

    await callback.answer("Tasdiqlandi")


# ================= REJECT PAYMENT =================

@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await db.delete_player(user_id)

    await callback.message.edit_caption(
        callback.message.caption + "\n\n❌ To'lov rad etildi"
    )

    await callback.bot.send_message(
        user_id,
        "❌ To'lovingiz rad etildi. Qayta yuboring."
    )

    await callback.answer("Rad etildi")


# ================= PLAYERS =================

@router.callback_query(F.data == "admin_players")
async def admin_players(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if not players:

        await callback.message.edit_text(
            "❌ Hali tasdiqlangan ishtirokchilar yo'q.",
            reply_markup=admin_menu()
        )

        await callback.answer()
        return

    for i, p in enumerate(players, 1):

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ O'chirish",
                        callback_data=f"delete_player_{p['user_id']}"
                    )
                ]
            ]
        )

        await callback.message.answer(
            f"""
👤 {i}-ishtirokchi

1️⃣ Ismi: {p['full_name']}
2️⃣ eFootball username: {p['username']}
3️⃣ Telegram: https://t.me/{p['telegram_username']}
""",
            reply_markup=keyboard
        )

    await callback.answer()


# ================= DELETE PLAYER =================

@router.callback_query(F.data.startswith("delete_player_"))
async def delete_player(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[2])

    await db.delete_player(user_id)

    await callback.message.edit_text(
        "❌ Ishtirokchi turnirdan o'chirildi."
    )

    await callback.bot.send_message(
        user_id,
        "❌ Siz turnirdan chiqarildingiz."
    )

    await callback.answer("O'chirildi")


# ================= STATISTICS =================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):

    total, paid, waiting = await db.get_statistics()

    text = f"""
📊 STATISTIKA

👥 Jami ro'yxatdan o'tgan: {total}
✅ To'lov qilgan: {paid}
⏳ Tekshirilmagan: {waiting}
"""

    await callback.message.edit_text(
        text,
        reply_markup=admin_menu()
    )

    await callback.answer()