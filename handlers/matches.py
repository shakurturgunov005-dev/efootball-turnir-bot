from aiogram import Router, types, F
from aiogram.filters import Command
from database import db

router = Router()


# ================= BRACKET =================

@router.message(Command("bracket"))
async def show_bracket(message: types.Message):

    players = await db.get_all_players(paid_only=True)

    if len(players) < 2:
        await message.answer(
            "❌ Turnir boshlanishi uchun kamida 2 ishtirokchi kerak."
        )
        return

    text = "🏆 TURNIR ISHTIROKCHILARI\n\n"

    for i, p in enumerate(players, 1):
        text += f"{i}. {p['full_name']}\n"

    await message.answer(text)


# ================= MATCHES =================

@router.message(Command("matches"))
async def show_matches(message: types.Message):

    await message.answer(
        "⚽️ Matchlar hali yaratilmagan.\n\n"
        "Turnir boshlangandan keyin chiqadi."
    )


# ================= CREATE MATCH =================

@router.message(F.text == "⚽️ Match yaratish")
async def create_match_prompt(message: types.Message):

    from config import ADMIN_IDS
    import random

    if message.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players(paid_only=True)

    if len(players) < 2:
        await message.answer(
            "❌ Match yaratish uchun kamida 2 ishtirokchi kerak."
        )
        return

    player1, player2 = random.sample(players, 2)

    await message.answer(
        f"⚽️ Test match\n\n"
        f"{player1['full_name']} vs {player2['full_name']}"
    )


# ================= SCORE =================

@router.message(Command("score"))
async def update_score(message: types.Message):

    from config import ADMIN_IDS

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "⚠️ Match tizimi hali yoqilmagan.\n"
        "Keyingi update da qo‘shiladi."
    )


# ================= STANDINGS =================

@router.message(Command("standings"))
async def show_standings(message: types.Message):

    players = await db.get_all_players(paid_only=True)

    if not players:
        await message.answer("❌ Hali ishtirokchilar yo'q.")
        return

    text = "🏆 TURNIR ISHTIROKCHILARI\n\n"

    for i, p in enumerate(players, 1):
        text += f"{i}️⃣ {p['full_name']}\n"

    await message.answer(text)