import os
from dotenv import load_dotenv

load_dotenv()

# Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Turnir sozlamalari
MAX_PLAYERS = 16

# To'lov ma'lumotlari
CARD_NUMBER = "2202 2063 4229 7533"
CARD_HOLDER = "SHUKURULLO TURGUNOV"
PAYMENT_AMOUNT = 300
RUB = "₽"