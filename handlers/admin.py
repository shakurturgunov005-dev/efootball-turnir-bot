from aiogram import Router, types, F  
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton  
from database import db  
from config import ADMIN_IDS, MAX_PLAYERS  

router = Router()


def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ishtirokchilar")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Post yuborish")],
            [KeyboardButton(text="💰 To'lov tekshirish")],
            [KeyboardButton(text="⚽️ Match yaratish")],
            [KeyboardButton(text="📝 Ro'yxatni tahrirlash")],
            [KeyboardButton(text="🗑 Tozalash")]
        ],
        resize_keyboard=True
    )


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

    await message.answer(text, parse_mode="Markdown")


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

    await message.answer(text, parse_mode="Markdown")


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
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        if row['payment_photo']:
            await message.bot.send_photo(
                message.chat.id,
                row['payment_photo'],
                caption="📸 To'lov cheki"
            )


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
            f"✅ Tabriklaymiz!\n\nTo'lovingiz tasdiqlandi.\nSiz {count}-ishtirokchi bo'ldingiz!",
            parse_mode="Markdown"
        )
    except:
        pass

    await callback.message.edit_text(f"✅ To'lov tasdiqlandi: {user['full_name']}")
    await callback.answer("✅ Tasdiqlandi")


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
            "❌ To'lov qabul qilinmadi.\n\nIltimos qayta yuboring.",
            parse_mode="Markdown"
        )
    except:
        pass

    await callback.message.edit_text("❌ To'lov rad etildi")
    await callback.answer()


@router.message(F.text == "📢 Post yuborish")
async def send_post(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players(paid_only=True)

    if not players:
        await message.answer("📭 Hali ishtirokchilar yo'q.")
        return

    text = "━━━━━━━━━━━━━━━━━━\n📋 TURNIR RO'YXATI\n━━━━━━━━━━━━━━━━━━\n\n"

    for i, player in enumerate(players, 1):
        text += f"{i}. {player['full_name']}\n"

    text += "\n━━━━━━━━━━━━━━━━━━"

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
        reply_markup=keyboard,
        parse_mode="Markdown"
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

    await callback.message.edit_text("✅ Barcha ma'lumotlar 1 sekundda tozalandi!")


@router.callback_query(F.data == "clear_no")
async def clear_no(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return

    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer(