import asyncpg
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        """Ma'lumotlar bazasiga ulanish havzasini yaratish"""
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.init_db()

    async def init_db(self):
        """Jadvallarni yaratish (mavjud bo'lmasa)"""
        async with self.pool.acquire() as conn:
            # Ishtirokchilar jadvali
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id SERIAL PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    telegram_username TEXT NOT NULL,
                    user_id BIGINT UNIQUE,
                    payment_status BOOLEAN DEFAULT FALSE,
                    payment_photo TEXT,
                    registered_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Matchlar jadvali
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id SERIAL PRIMARY KEY,
                    player1_id INTEGER REFERENCES players(id),
                    player2_id INTEGER REFERENCES players(id),
                    round INTEGER,
                    match_time TIMESTAMP,
                    score TEXT,
                    winner_id INTEGER REFERENCES players(id),
                    status TEXT DEFAULT 'pending'
                )
            """)

    # ========== ISHTIROKCHILAR BILAN ISHLASH ==========
    
    async def add_player(self, full_name, username, telegram_username, user_id):
        """Yangi ishtirokchi qo'shish"""
        async with self.pool.acquire() as conn:
            return await conn.execute("""
                INSERT INTO players (full_name, username, telegram_username, user_id) 
                VALUES ($1, $2, $3, $4)
            """, full_name, username, telegram_username, user_id)

    async def get_player_by_user_id(self, user_id):
        """User ID bo'yicha ishtirokchini topish"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM players WHERE user_id = $1", user_id
            )

    async def get_all_players(self, paid_only=False):
        """Barcha ishtirokchilarni olish"""
        async with self.pool.acquire() as conn:
            if paid_only:
                return await conn.fetch(
                    "SELECT * FROM players WHERE payment_status = TRUE ORDER BY id"
                )
            return await conn.fetch("SELECT * FROM players ORDER BY id")

    async def update_payment_status(self, user_id, photo_id=None):
        """To'lov statusini yangilash"""
        async with self.pool.acquire() as conn:
            if photo_id:
                await conn.execute("""
                    UPDATE players 
                    SET payment_photo = $1 
                    WHERE user_id = $2
                """, photo_id, user_id)
            else:
                await conn.execute("""
                    UPDATE players 
                    SET payment_status = TRUE 
                    WHERE user_id = $1
                """, user_id)

    async def delete_player(self, user_id):
        """Ishtirokchini o'chirish"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM players WHERE user_id = $1", user_id
            )

    async def get_statistics(self):
        """Statistika ma'lumotlarini olish"""
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM players")
            paid = await conn.fetchval(
                "SELECT COUNT(*) FROM players WHERE payment_status = TRUE"
            )
            waiting = await conn.fetchval(
                "SELECT COUNT(*) FROM players WHERE payment_status = FALSE AND payment_photo IS NOT NULL"
            )
            return total, paid, waiting

    # ========== MATCHLAR BILAN ISHLASH ==========
    
    async def create_match(self, player1_id, player2_id, round_num, match_time):
        """Yangi match yaratish"""
        async with self.pool.acquire() as conn:
            return await conn.execute("""
                INSERT INTO matches (player1_id, player2_id, round, match_time)
                VALUES ($1, $2, $3, $4)
            """, player1_id, player2_id, round_num, match_time)

    async def update_match_score(self, match_id, score, winner_id):
        """Match natijasini yangilash"""
        async with self.pool.acquire() as conn:
            return await conn.execute("""
                UPDATE matches 
                SET score = $1, winner_id = $2, status = 'completed'
                WHERE id = $3
            """, score, winner_id, match_id)

    async def get_matches(self):
        """Barcha matchlarni olish"""
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM matches ORDER BY round, id")

    async def close(self):
        """Ulanish havzasini yopish"""
        if self.pool:
            await self.pool.close()

# Global database obyekti
db = Database()