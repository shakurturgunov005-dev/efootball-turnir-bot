from aiogram import Router, types, F
from aiogram.filters import Command
from database import db
from datetime import datetime

router = Router()

@router.message(Command("bracket"))
async def show_bracket(message: types.Message):
    """Turnir jadvalini ko'rsatish"""
    
    # To'lov qilgan ishtirokchilarni olish
    players = await db.get_all_players(paid_only=True)
    
    if len(players) < 2:
        await message.answer("❌ Turnir boshlanishi uchun kamida 2 ishtirokchi kerak.")
        return
    
    # Jadvalni yaratish
    from utils.bracket import create_bracket
    bracket_text = create_bracket(players)
    
    await message.answer(f"<pre>{bracket_text}</pre>", parse_mode="HTML")

@router.message(Command("matches"))
async def show_matches(message: types.Message):
    """Matchlar ro'yxatini ko'rsatish"""
    
    matches = await db.get_matches()
    
    if not matches:
        await message.answer("⚽️ Hali matchlar yaratilmagan.")
        return
    
    text = "⚽️ **MATCHLAR**\n\n"
    
    for match in matches:
        # Ishtirokchilarni olish
        p1 = "Noma'lum"
        p2 = "Noma'lum"
        
        # Bu yerda player ma'lumotlarini olish kerak
        # Soddalashtirilgan versiya
        
        match_time = match['match_time'].strftime("%d.%m %H:%M") if match['match_time'] else "Vaqt belgilanmagan"
        score = match['score'] if match['score'] else "— : —"
        status = "✅" if match['status'] == 'completed' else "⏳"
        
        text += f"{status} {p1} vs {p2}\n   🕐 {match_time} | {score}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

# Admin uchun match yaratish
@router.message(F.text == "⚽️ Match yaratish")
async def create_match_prompt(message: types.Message):
    """Admin match yaratishni boshlash"""
    
    from config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # To'lov qilgan ishtirokchilarni olish
    players = await db.get_all_players(paid_only=True)
    
    if len(players) < 2:
        await message.answer("❌ Match yaratish uchun kamida 2 ishtirokchi kerak.")
        return
    
    # Bu yerda match yaratish interfeysi bo'lishi mumkin
    # Soddalashtirilgan versiya
    await message.answer("⚽️ Match yaratish funksiyasi ishlab chiqilmoqda...")

@router.message(Command("score"))
async def update_score(message: types.Message):
    """Match natijasini yangilash (admin uchun)"""
    
    from config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Format: /score 123 3:2 456
    # 123 - match ID, 3:2 - hisob, 456 - g'olib ID
    
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
