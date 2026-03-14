from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import db
from config import ADMIN_IDS, MAX_PLAYERS, CHANNEL_ID
import random

router = Router()


# ================= MATCH GENERATOR =================

async def generate_matches():

    players = await db.get_all_players(paid_only=True)

    players = list(players)
    random.shuffle(players)

    async with db.pool.acquire() as conn:

        for i in range(0, len(players), 2):

            if i + 1 >= len(players):
                break

            p1 = players[i]["user_id"]
            p2 = players[i + 1]["user_id"]

            await conn.execute(
                """
                INSERT INTO matches (player1, player2, round)
                VALUES ($1,$2,$3)
                """,
                p1, p2, "1_8"
            )


# ================= ADMIN MENU =================

def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ishtirokchilar", callback_data="admin_players")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Post yuborish", callback_data="admin_post")],
            [InlineKeyboardButton(text="💰 To'lov tekshirish", callback_data="admin_payments")],
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


# ================= PLAYERS =================

@router.callback_query(F.data == "admin_players")
async def show_players(callback: types.CallbackQuery):

    players = await db.get_all_players()

    if not players:
        await callback.message.edit_text(
            "📭 Hali ishtirokchilar yo'q.",
            reply_markup=admin_menu()
        )
        await callback.answer()
        return

    text = "📋 ISHTIROKCHILAR\n\n"

    keyboard = []

    for p in players:

        username = f"@{p['username']}" if p['username'] else "username yo'q"

        text += f"{p['id']}. {p['full_name']} - {username}\n"

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"❌ {p['full_name']} ni o'chirish",
                    callback_data=f"delete_{p['user_id']}"
                )
            ]
        )

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

    async with db.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM players WHERE user_id=$1",
            user_id
        )

    await callback.answer("✅ Ishtirokchi o'chirildi", show_alert=True)

    players = await db.get_all_players()

    text = "📋 ISHTIROKCHILAR\n\n"

    for p in players:

        username = f"@{p['username']}" if p['username'] else "username yo'q"

        text += f"{p['id']}. {p['full_name']} - {username}\n"

    await callback.message.edit_text(text)


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
━━━━━━━━━━━━━━━━━━
👥 Jami ro'yxatdan o'tgan: {total}
✅ To'lov qilgan: {paid}
⏳ Tekshirilmagan: {waiting}
🕐 Bo'sh joy: {MAX_PLAYERS - paid}
━━━━━━━━━━━━━━━━━━
"""

    await callback.message.edit_text(text, reply_markup=admin_menu())
    await callback.answer()


# ================= POST =================

@router.callback_query(F.data == "admin_post")
async def send_post(callback: types.CallbackQuery):

    players = await db.get_all_players()
    count = len(players)

    text = f"""
🎮 eFootball TURNIR BOTI 🤖

🏆 Professional eFootball turniriga xush kelibsiz!

👥 Ishtirokchilar: {count} / {MAX_PLAYERS}
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


# ================= MATCH CREATE =================

@router.callback_query(F.data == "admin_match")
async def create_matches(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)

    if len(players) < MAX_PLAYERS:
        await callback.answer("❌ Yetarli o'yinchi yo'q", show_alert=True)
        return

    await generate_matches()

    text = "🏆 1/8 FINAL JUFTLIKLARI\n\n"

    async with db.pool.acquire() as conn:
        matches = await conn.fetch("SELECT * FROM matches WHERE round='1_8'")

    for i, match in enumerate(matches, 1):

        p1 = await db.get_player_by_user_id(match["player1"])
        p2 = await db.get_player_by_user_id(match["player2"])

        text += f"{i}. {p1['full_name']} ⚔️ {p2['full_name']}\n"

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
        await conn.execute(
            """
            TRUNCATE players, matches
            RESTART IDENTITY CASCADE
            """
        )

    await callback.message.edit_text("✅ Barcha ma'lumotlar tozalandi!")
    await callback.answer()


@router.callback_query(F.data == "clear_no")
async def clear_no(callback: types.CallbackQuery):

    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer()