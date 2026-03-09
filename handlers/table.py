from aiogram import Router
from aiogram.types import Message
from database import db

router = Router()


@router.message(lambda message: message.text == "/table")
async def show_table(message: Message):

    standings = await db.get_standings()

    if not standings:
        await message.answer("❌ Jadval hali shakllanmagan.")
        return

    text = "🏆 TURNIR JADVALI\n\n"

    place = 1

    for row in standings:
        text += (
            f"{place}. {row['full_name']}\n"
            f"⚽ O'yin: {row['played']} | "
            f"✅ {row['wins']} | "
            f"➖ {row['draws']} | "
            f"❌ {row['losses']}\n"
            f"🥅 {row['goals_for']}:{row['goals_against']} "
            f"({row['goal_diff']})\n"
            f"🏅 Ochko: {row['points']}\n\n"
        )

        place += 1

    await message.answer(text)