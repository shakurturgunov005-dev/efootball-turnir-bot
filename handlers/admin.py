from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS, CHANNEL_ID, MAX_PLAYERS

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

    player = await db.get_player_by_user_id(user_id)

    players = await db.get_all_players(paid_only=True)

    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ To'lov tasdiqlandi"
    )

    await callback.bot.send_message(
        user_id,
        "🎉 To'lovingiz tasdiqlandi! Siz turnirga qo'shildingiz."
    )

    text = f"""
🎮 Yangi ishtirokchi qo'shildi

👤 {player['full_name']}
⚽ eFootball: {player['username']}
📱 Telegram: https://t.me/{player['telegram_username']}

📊 Ishtirokchilar: {len(players)} / {MAX_PLAYERS}
"""

    try:
        await callback.bot.send_message(
            CHANNEL_ID,
            text
        )
    except:
        pass

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

    text = "👥 TASDIQLANGAN ISHTIROKCHILAR\n\n"

    keyboard = []

    for i, p in enumerate(players, 1):

        text += f"{i}. {p['full_name']} - https://t.me/{p['telegram_username']}\n"

        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {p['full_name']} ni o'chirish",
                callback_data=f"delete_{p['user_id']}"
            )
        ])

    keyboard.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await callback.answer()


# ================= DELETE PLAYER =================

@router.callback_query(F.data.startswith("delete_"))
async def delete_player(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await db.delete_player(user_id)

    await callback.answer("❌ Ishtirokchi o'chirildi", show_alert=True)

    players = await db.get_all_players(paid_only=True)

    text = "👥 TASDIQLANGAN ISHTIROKCHILAR\n\n"

    keyboard = []

    for i, p in enumerate(players, 1):

        text += f"{i}. {p['full_name']} - https://t.me/{p['telegram_username']}\n"

        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {p['full_name']} ni o'chirish",
                callback_data=f"delete_{p['user_id']}"
            )
        ])

    keyboard.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


# ================= BACK =================

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):

    await callback.message.edit_text(
        "👑 ADMIN PANEL",
        reply_markup=admin_menu()
    )

    await callback.answer()


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