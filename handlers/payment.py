from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import CARD_NUMBER, CARD_HOLDER, PAYMENT_AMOUNT, RUB, ADMIN_IDS
import asyncio

router = Router()


# ================= TO'LOVNI TASDIQLASH SAVOLI =================

@router.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: types.CallbackQuery):

    await callback.message.delete()

    payment_text = f"""
💳 TO'LOV MA'LUMOTLARI

Turnirda ishtirok etish uchun {PAYMENT_AMOUNT} {RUB} to'lashingiz kerak.

Karta raqami: {CARD_NUMBER}
Qabul qiluvchi: {CARD_HOLDER}

📌 To'lovni amalga oshirgach, chekni (skrinshot) shu yerga yuboring.

Admin tasdiqlagach siz turnirga qo'shilasiz.
"""

    await callback.message.answer(payment_text)
    await callback.answer()


# ================= RO'YXATNI BEKOR QILISH =================

@router.callback_query(F.data == "confirm_no")
async def confirm_no(callback: types.CallbackQuery):

    await callback.message.delete()

    cancel_msg = await callback.message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")
    await asyncio.sleep(5)

    await cancel_msg.delete()

    await db.delete_player(callback.from_user.id)

    await callback.answer()


# ================= CHEK QABUL QILISH =================

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

    # chekni saqlash
    await db.save_payment_photo(user_id, photo_id)

    await message.answer(
        "✅ To'lov cheki qabul qilindi. Admin tekshirgach, ro'yxatdan o'tasiz."
    )

    # ================= ADMINLARGA YUBORISH =================

    for admin_id in ADMIN_IDS:
        try:

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Tasdiqlash",
                            callback_data=f"approve_{user_id}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Rad etish",
                            callback_data=f"reject_{user_id}"
                        )
                    ]
                ]
            )

            await message.bot.send_photo(
                admin_id,
                photo_id,
                caption=f"""
💰 Yangi to'lov keldi!

👤 {user['full_name']}
🆔 {user_id}
""",
                reply_markup=keyboard
            )

        except Exception as e:
            print(e)


# ================= ADMIN TASDIQLASH =================

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await db.confirm_payment(user_id)

    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ To'lov tasdiqlandi"
    )

    await callback.bot.send_message(
        user_id,
        "🎉 To'lovingiz tasdiqlandi! Siz turnirga qo'shildingiz."
    )

    await callback.answer("Tasdiqlandi")


# ================= ADMIN RAD ETISH =================

@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await db.delete_player(user_id)

    await callback.message.edit_caption(
        callback.message.caption + "\n\n❌ To'lov rad etildi"
    )

    await callback.bot.send_message(
        user_id,
        "❌ To'lovingiz rad etildi. Qayta yuboring."
    )

    await callback.answer("Rad etildi")


# ================= KUTILAYOTGAN TO'LOVLAR =================

@router.callback_query(F.data == "pending_payments")
async def pending_payments(callback: types.CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Siz admin emassiz", show_alert=True)
        return

    players = await db.get_all_players()

    pending = [p for p in players if not p["payment_status"]]

    if not pending:
        text = "⌛ Tasdiqlanishi kutilayotgan to'lovlar yo'q."
    else:

        text = "⌛ Tasdiqlanishi kutilayotganlar\n\n"

        for p in pending:
            text += f"""
👤 {p['full_name']}
🆔 {p['user_id']}
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()