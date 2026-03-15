import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

ADMIN_IDS = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip()
]

DATABASE_URL = os.getenv("DATABASE_URL")

MAX_PLAYERS = 16

CARD_NUMBER = "2202 2063 4229 7533"
CARD_HOLDER = "SHUKURULLO TURGUNOV"
PAYMENT_AMOUNT = 300
RUB = "₽"
print("DEBUG ADMIN_IDS =", ADMIN_IDS)
GROUP_ID = int(os.getenv("GROUP_ID", "0"))