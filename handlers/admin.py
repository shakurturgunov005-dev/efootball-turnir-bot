from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS, MAX_PLAYERS

router = Router()


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
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_menu"
                )
            ]

        ]
    )

    return keyboard


# ================= ADMIN PANEL =================

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        return

    await callback.message.edit_text(
        "👑 ADMIN PANEL",
        reply_markup=admin_menu()
    )

    await callback.answer()


# ================= STATISTIKA =================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):

    total, paid, waiting = await db.get_statistics()

    text = f"""
📊 STATISTIKA

👥 Jami ro'yxatdan o'tgan: {total}
✅ To'lov qilgan: {paid}
⏳ Tekshirilmagan: {waiting}
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="admin_panel"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# ================= ISHTIROKCHILAR =================

@router.callback_query(F.data == "admin_players")
async def admin_players(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if not players:

        await callback.message.edit_text(
            "❌ Hali ishtirokchilar yo'q.",
            reply_markup=admin_menu()
        )

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

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="admin_panel"
        )
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await callback.answer()


# ================= PLAYER DELETE =================

@router.callback_query(F.data.startswith("delete_"))
async def delete_player(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await db.delete_player(user_id)

    await callback.answer(
        "❌ Ishtirokchi o'chirildi",
        show_alert=True
    )

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

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="admin_panel"
        )
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


# ================= BACK MENU =================

@router.callback_query(F.data == "back_menu")
async def back_menu(callback: types.CallbackQuery):

    from handlers.user import main_menu

    players = await db.get_all_players(paid_only=True)
    players_count = len(players)

    await callback.message.edit_text(
        "🏠 Bosh menyu",
        reply_markup=main_menu(callback.from_user.id, players_count)
    )

    await callback.answer()