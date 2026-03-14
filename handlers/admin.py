from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import db
from config import ADMIN_IDS, MAX_PLAYERS, CHANNEL_ID
import random

router = Router()


# ================= ADMIN MENU =================

def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ishtirokchilar", callback_data="admin_players")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Post yuborish", callback_data="admin_post")],
            [InlineKeyboardButton(text="⚽ Match yaratish", callback_data="admin_match")],
            [InlineKeyboardButton(text="🗑 Tozalash", callback_data="admin_clear")]
        ]
    )


# ================= ADMIN PANEL =================

@router.message(Command("admin"))
async def admin_panel(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "👑 ADMIN PANEL",
        reply_markup=admin_menu()
    )


# ================= PLAYERS LIST =================

@router.callback_query(F.data == "admin_players")
async def show_players(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if not players:
        await callback.message.edit_text(
            "📭 Hali tasdiqlangan ishtirokchilar yo'q.",
            reply_markup=admin_menu()
        )
        await callback.answer()
        return

    text = "👥 ISHTIROKCHILAR RO'YXATI\n\n"

    for i, p in enumerate(players, 1):

        tg = p["telegram_username"].replace("@", "")
        link = f"https://t.me/{tg}"

        text += (
            f"№ {i}\n"
            f"1️⃣ Ismi: {p['full_name']}\n"
            f"2️⃣ eFootball username: {p['username']}\n"
            f"3️⃣ Telegram:\n{link}\n\n"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Edit", callback_data="admin_edit")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ================= EDIT MODE =================

@router.callback_query(F.data == "admin_edit")
async def edit_players(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    text = "🗑 O'chirish uchun ishtirokchini tanlang\n\n"

    keyboard = []

    for p in players:

        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {p['full_name']}",
                callback_data=f"delete_{p['user_id']}"
            )
        ])

    keyboard.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_players")]
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

    async with db.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM players WHERE user_id=$1",
            user_id
        )

    await callback.answer("✅ Ishtirokchi o'chirildi", show_alert=True)

    players = await db.get_all_players(paid_only=True)

    keyboard = []

    for p in players:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {p['full_name']}",
                callback_data=f"delete_{p['user_id']}"
            )
        ])

    keyboard.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_players")]
    )

    await callback.message.edit_text(
        "🗑 O'chirish uchun ishtirokchini tanlang",
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
async def show_stats(callback: types.CallbackQuery):

    total, paid, waiting = await db.get_statistics()

    text = f"""
📊 STATISTIKA

👥 Jami ro'yxatdan o'tgan: {total}
✅ To'lov qilgan: {paid}
⏳ Tekshirilmagan: {waiting}
🪑 Bo'sh joy: {MAX_PLAYERS - paid}
"""

    await callback.message.edit_text(
        text,
        reply_markup=admin_menu()
    )

    await callback.answer()


# ================= POST =================

@router.callback_query(F.data == "admin_post")
async def send_post(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)
    count = len(players)

    text = f"""
🎮 eFootball TURNIR BOTI

🏆 Professional eFootball turniri

👥 Ishtirokchilar: {count}/{MAX_PLAYERS}

🔥 Ro'yxatdan o'tish ochiq
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚽ Turnirga qatnashish", callback_data="register")]
        ]
    )

    await callback.bot.send_message(
        CHANNEL_ID,
        text,
        reply_markup=keyboard
    )

    await callback.answer("Post yuborildi")


# ================= MATCH GENERATE =================

@router.callback_query(F.data == "admin_match")
async def create_matches(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if len(players) < MAX_PLAYERS:
        await callback.answer("❌ Yetarli o'yinchi yo'q", show_alert=True)
        return

    random.shuffle(players)

    text = "🏆 1/8 FINAL JUFTLIKLARI\n\n"

    for i in range(0, len(players), 2):

        p1 = players[i]["full_name"]
        p2 = players[i+1]["full_name"]

        text += f"{p1} ⚔️ {p2}\n"

    await callback.message.answer(text)
    await callback.bot.send_message(CHANNEL_ID, text)

    await callback.answer()


# ================= CLEAR DATABASE =================

@router.callback_query(F.data == "admin_clear")
async def clear_all(callback: types.CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="clear_yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="clear_no")
            ]
        ]
    )

    await callback.message.edit_text(
        "⚠️ Barcha ma'lumotlarni tozalashni xohlaysizmi?",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "clear_yes")
async def clear_yes(callback: types.CallbackQuery):

    async with db.pool.acquire() as conn:
        await conn.execute("""
        TRUNCATE players, matches
        RESTART IDENTITY CASCADE
        """)

    await callback.message.edit_text("✅ Barcha ma'lumotlar tozalandi!")
    await callback.answer()


@router.callback_query(F.data == "clear_no")
async def clear_no(callback: types.CallbackQuery):

    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer()