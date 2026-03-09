from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import ADMIN_IDS, MAX_PLAYERS, CHANNEL_ID
import random

router = Router()


# MATCH GENERATOR
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


# ADMIN KEYBOARD
def admin_keyboard():
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


# PLAYERS LIST
@router.message(F.text == "📋 Ishtirokchilar")
async def show_players(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players(paid_only=True)

    if not players:
        await message.answer("📭 Hali ishtirokchilar yo'q.")
        return

    text = f"📋 Ishtirokchilar ({len(players)}/{MAX_PLAYERS})\n\n"

    for p in players:
        username = f"@{p['username']}" if p['username'] else "username yo'q"
        text += f"{p['id']}. {p['full_name']} - {username}\n   ✅ To'lov qilingan\n\n"

    await message.answer(text)


# STATISTICS
@router.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

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

    await message.answer(text)


# PAYMENT CHECK
@router.message(F.text == "💰 To'lov tekshirish")
async def check_payments(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM players WHERE payment_status = FALSE AND payment_photo IS NOT NULL"
        )

    if not rows:
        await message.answer("📭 Tekshirilmagan to'lovlar yo'q.")
        return

    for row in rows:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{row['user_id']}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{row['user_id']}")
                ]
            ]
        )

        await message.answer(
            f"💰 Yangi to'lov\n\n👤 {row['full_name']}\n🆔 {row['user_id']}",
            reply_markup=keyboard
        )

        if row['payment_photo']:
            await message.bot.send_photo(
                message.chat.id,
                row['payment_photo'],
                caption="📸 To'lov cheki"
            )


# CONFIRM PAYMENT
@router.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    user_id = int(callback.data.replace("confirm_", ""))

    await db.update_payment_status(user_id)

    user = await db.get_player_by_user_id(user_id)

    paid_players = await db.get_all_players(paid_only=True)
    count = len(paid_players)

    try:
        await callback.bot.send_message(
            user_id,
            f"✅ Tabriklaymiz!\n\nTo'lovingiz tasdiqlandi.\nSiz {count}-ishtirokchi bo'ldingiz!"
        )
    except:
        pass

    await callback.message.edit_text(f"✅ To'lov tasdiqlandi: {user['full_name']}")
    await callback.answer("✅ Tasdiqlandi")


# REJECT PAYMENT
@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    user_id = int(callback.data.replace("reject_", ""))

    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE players SET payment_photo=NULL WHERE user_id=$1",
            user_id
        )

    try:
        await callback.bot.send_message(
            user_id,
            "❌ To'lov qabul qilinmadi.\n\nIltimos qayta yuboring."
        )
    except:
        pass

    await callback.message.edit_text("❌ To'lov rad etildi")
    await callback.answer()


# TOURNAMENT POST
@router.message(F.text == "📢 Post yuborish")
async def send_post(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players()
    count = len(players)

    text = f"""
🎮 eFootball TURNIR BOTI 🤖

🏆 Professional eFootball turniriga xush kelibsiz!

👥 Ishtirokchilar: {count} / {MAX_PLAYERS}

ℹ️ Eslatma: turnirda ishtirok etish uchun badal miqdori 300₽ etib belgilangan.
To'lov tasdiqlangandan so'ng ishtirokchi turnir ro'yxatiga kiritiladi.

🔥 Eng kuchlilar finalga chiqadi!
"""

    if count == MAX_PLAYERS - 1:
        text += "\n\n⚠️ Oxirgi joy qoldi!"

    if count >= MAX_PLAYERS:
        text += "\n\n❌ Ro'yxatdan o'tish yopildi!"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚽️ Turnirga qatnashish",
                    callback_data="register"
                )
            ]
        ]
    )

    await message.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        reply_markup=keyboard
    )

    await message.answer("✅ Turnir posti kanalga yuborildi!")


# CREATE MATCHES
@router.message(F.text == "⚽️ Match yaratish")
async def create_matches(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players(paid_only=True)

    if len(players) < MAX_PLAYERS:
        await message.answer(
            f"❌ Hali yetarli o'yinchi yo'q.\n\nKerak: {MAX_PLAYERS}\nHozir: {len(players)}"
        )
        return

    await generate_matches()

    text = "🏆 1/8 FINAL JUFTLIKLARI\n\n"

    async with db.pool.acquire() as conn:
        matches = await conn.fetch("SELECT * FROM matches WHERE round='1_8'")

    for i, match in enumerate(matches, 1):

        p1 = await db.get_player_by_user_id(match["player1"])
        p2 = await db.get_player_by_user_id(match["player2"])

        text += f"{i}. {p1['full_name']} ⚔️ {p2['full_name']}\n"

    await message.answer(text)

    await message.bot.send_message(
        CHANNEL_ID,
        text
    )


# CLEAR DATABASE
@router.message(F.text == "🗑 Tozalash")
async def clear_all(message: types.Message):

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

    await message.answer(
        "⚠️ Barcha ma'lumotlarni tozalashni xohlaysizmi?",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "clear_yes")
async def clear_yes(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    await callback.answer("🧹 Ma'lumotlar tozalanmoqda...")

    async with db.pool.acquire() as conn:
        await conn.execute("""
        TRUNCATE players, matches
        RESTART IDENTITY CASCADE
        """)

    await callback.message.edit_text("✅ Barcha ma'lumotlar tozalandi!")


@router.callback_query(F.data == "clear_no")
async def clear_no(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return

    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer()