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
    player_dict = {p['id']: p['full_name'] for p in players}
    text = "⚽️ **MATCHLAR**\n\n"
    for match in matches:
        p1 = player_dict.get(match['player1_id'], "Noma'lum")
        p2 = player_dict.get(match['player2_id'], "Noma'lum")
        match_time = match['match_time'].strftime("%d.%m %H:%M") if match['match_time'] else "Vaqt belgilanmagan"
        score = match['score'] if match['score'] else "— : —"
        status = "✅" if match['status'] == 'completed' else "⏳"
        text += f"{status} {p1} vs {p2}\n   🕐 {match_time} | {score}\n\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "⚽️ Match yaratish")
async def create_match_prompt(message: types.Message):
    from config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        return
    players = await db.get_all_players(paid_only=True)
    if len(players) < 2:
        await message.answer("❌ Match yaratish uchun kamida 2 ishtirokchi kerak.")
        return
    await message.answer("⚽️ Match yaratish funksiyasi ishlab chiqilmoqda...")

@router.message(Command("score"))
async def update_score(message: types.Message):
    from config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()[1:]
    if len(args) < 3:
        await message.answer("❌ Format: /score [match_id] [hisob] [winner_id]")
        return
    try:
        match_id = int(args[0])
        score = args[1]
        winner_id = int(args[2])
        await db.update_match_score(match_id, score, winner_id)
        await message.answer(f"✅ Match natijasi yangilandi: {score}")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")