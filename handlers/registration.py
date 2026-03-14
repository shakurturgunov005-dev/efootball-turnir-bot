from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import MAX_PLAYERS

router = Router()


REGISTRATION_TEMPLATE = """
📝 **TURNIRGA RO'YXATDAN O'TISH**

1️⃣ Ismingiz :
2️⃣ eFootball username :
3️⃣ Telegram username :

📌 To'ldirib, shu botga qayta yuboring.
"""


@router.callback_query(F.data == "register")
async def register_start(callback: types.CallbackQuery):

    players = await db.get_all_players(paid_only=True)
    count = len(players)

    if count >= MAX_PLAYERS:

        await callback.message.answer(
            f"""
❌ Turnir uchun joy qolmadi.

🏆 {MAX_PLAYERS}/{MAX_PLAYERS} ishtirokchi to'lgan.
"""
        )

        await callback.answer()
        return

    await callback.message.answer(
        REGISTRATION_TEMPLATE,
        parse_mode="Markdown"
    )

    await callback.answer()


@router.message(
    F.text.contains("1️⃣") &
    F.text.contains("2️⃣") &
    F.text.contains("3️⃣")
)
async def handle_registration(message: types.Message):

    text = message.text.strip()
    lines = text.split('\n')

    if len(lines) < 3:
        await message.answer(
            "❌ Noto'g'ri format. Shablon bo'yicha to'ldiring."
        )
        return

    full_name = ""
    username = ""
    telegram_username = ""

    for line in lines:

        if "1️⃣" in line:
            full_name = line.split(":", 1)[-1].strip()

        elif "2️⃣" in line:
            username = line.split(":", 1)[-1].strip()

        elif "3️⃣" in line:
            telegram_username = line.split(":", 1)[-1].strip()

    existing = await db.get_player_by_user_id(message.from_user.id)

    if existing:
        await message.answer("❌ Siz avval ro'yxatdan o'tgansiz!")
        return

    await db.add_player(
        full_name,
        username,
        telegram_username,
        message.from_user.id
    )

    # HOZIRGI RO'YXAT SONI
    players = await db.get_all_players()
    count = len(players)

    await message.answer(
        f"""
✅ Yangi ishtirokchi qo'shildi

📊 Hozir: {count}/{MAX_PLAYERS}
"""
    )

    # TURNIR TO'LGANI
    if count >= MAX_PLAYERS:

        await message.answer(
            f"""
🏆 Turnir uchun {MAX_PLAYERS} ishtirokchi to‘ldi!

⚽ Turnir boshlandi
"""
        )

    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ HA, o'zim xohlayman",
                    callback_data="confirm_yes"
                ),
                InlineKeyboardButton(
                    text="❌ YO'Q",
                    callback_data="confirm_no"
                )
            ]
        ]
    )

    await message.answer(
        "⚠️ To'lovni o'zingiz xohlab qilyapsizmi?",
        reply_markup=confirm_keyboard
    )