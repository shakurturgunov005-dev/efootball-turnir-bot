from aiogram import Router, types, F
from aiogram.filters import Command
from database import db
from datetime import datetime

router = Router()


@router.message(Command("bracket"))
async def show_bracket(message: types.Message):
    players = await db.get_all_players(paid_only=True)

    if len(players) < 2:
        await message.answer("❌ Turnir boshlanishi uchun kamida 2 ishtirokchi kerak.")
        return

    from utils.bracket import create_bracket

    bracket_text = create_bracket(players)

    await message.answer(f"<pre>{bracket_text}</pre>", parse_mode="HTML")


@router.message(Command("matches"))
async def show_matches(message: types.Message):
    matches = await db.get_matches()

    if not matches:
        await message.answer("⚽️ Hali matchlar yaratilmagan.")
        return

    players = await db.get_all_players(paid_only=True)
    player_dict = {p["id"]: p["full_name"] for p in players}

    text = "⚽️ **MATCHLAR**\n\n"

    for match in matches:
        p1 = player_dict.get(match["player1_id"], "Noma'lum")
        p2 = player_dict.get(match["player2_id"], "Noma'lum")

        match_time = (
            match["match_time"].strftime("%d.%m %H:%M")
            if match["match_time"]
            else "Vaqt belgilanmagan"
        )

        score = match["score"] if match["score"] else "— : —"

        status = "✅" if match["status"] == "completed" else "⏳"

        text += f"{status} {p1} vs {p2}\n"
        text += f"   🕐 {match_time} | {score}\n\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "⚽️ Match yaratish")
async def create_match_prompt(message: types.Message):
    from config import ADMIN_IDS
    import random

    if message.from_user.id not in ADMIN_IDS:
        return

    players = await db.get_all_players(paid_only=True)

    if len(players) < 2:
        await message.answer("❌ Match yaratish uchun kamida 2 ishtirokchi kerak.")
        return

    player1, player2 = random.sample(players, 2)

    await db.create_match(player1["id"], player2["id"])

    await message.answer(
        f"⚽️ Yangi match yaratildi!\n\n"
        f"{player1['full_name']} vs {player2['full_name']}"
    )
    
@router.message(Command("score"))
async def update_score(message: types.Message):
    from config import ADMIN_IDS
    import re

    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split()[1:]

    if len(args) < 2:
        await message.answer("❌ Format: /score [match_id] [hisob]")
        return

    try:
        match_id = int(args[0])
        score = args[1]

        # Score format tekshirish
        if not re.match(r"^\d+:\d+$", score):
            await message.answer(
                "❌ Score noto‘g‘ri formatda!\n\n"
                "To‘g‘ri format:\n"
                "5:3"
            )
            return

        score1, score2 = map(int, score.split(":"))

        match = await db.get_match(match_id)

        if not match:
            await message.answer("❌ Match topilmadi.")
            return

        # G‘olibni aniqlash
        if score1 > score2:
            winner_id = match["player1_id"]
        elif score2 > score1:
            winner_id = match["player2_id"]
        else:
            await message.answer("❌ Durang bo‘lishi mumkin emas!")
            return

        await db.update_match_score(match_id, score, winner_id)

        await message.answer(
            f"✅ Match natijasi yangilandi\n"
            f"Score: {score}"
        )

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi:\n{e}")
        
@router.message(Command("matches"))
async def show_matches(message: types.Message):

    matches = await db.get_matches_with_players()

    if not matches:
        await message.answer("❌ Hali matchlar yo‘q.")
        return

    text = "⚽ Matchlar ro‘yxati:\n\n"

    for m in matches:
        text += f"{m['id']}️⃣ {m['player1']} vs {m['player2']}\n"

    await message.answer(text)