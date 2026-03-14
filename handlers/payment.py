from aiogram import Router, types, F
from database import db
from config import CARD_NUMBER, CARD_HOLDER, PAYMENT_AMOUNT, RUB, ADMIN_IDS
import asyncio

router = Router()


@router.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: types.CallbackQuery):

    await callback.message.delete()

    payment_text = f"""
💳 **TO'LOV MA'LUMOTLARI**

Turnirda ishtirok etish uchun {PAYMENT_AMOUNT} {RUB} to'lashingiz kerak.

**Karta raqami:** `{CARD_NUMBER}`
**Qabul qiluvchi:** {CARD_HOLDER}

📌 To'lovni amalga oshirgach, **chekni (skrinshot)** shu yerga yuboring.

Admin to'lovni tasdiqlagach, ro'yxatdan o'tgan hisoblanasiz.
"""

    await callback.message.answer(payment_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "confirm_no")
async def confirm_no(callback: types.CallbackQuery):

    await callback.message.delete()

    cancel_msg = await callback.message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")
    await asyncio.sleep(5)

    await cancel_msg.delete()

    await db.delete_player(callback.from_user.id)

    await callback.answer()


@router.message(F.photo)
async def handle_payment_photo(message: types.Message):

    user_id = message.from_user.id
    user = await db.get_player_by_user_id(user_id)

    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting!")
        return

    if user['payment_status']:
        await message.answer("✅ Sizning to'lovingiz allaqachon tasdiqlangan!")
        return

    photo_id = message.photo[-1].file_id

    await db.update_payment_status(user_id, photo_id)

    await message.answer(
        "✅ To'lov cheki qabul qilindi. Admin tekshirgach, ro'yxatdan o'tasiz."
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"💰 **Yangi to'lov keldi!**\n\n👤 {user['full_name']}\n🆔 {user_id}",
                parse_mode="Markdown"
            )

            await message.bot.send_photo(admin_id, photo_id)

        except:
            pass