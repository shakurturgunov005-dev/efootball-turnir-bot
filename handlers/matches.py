from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("match"))
async def match_cmd(message: Message):
    await message.answer("Match bo‘limi hali tayyorlanmoqda ⚽")