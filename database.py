import asyncpg
from config import DATABASE_URL


class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.init_db()

    async def init_db(self):
        async with self.pool.acquire() as conn:

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

    # ================= PLAYERS =================

    async def add_player(self, full_name, username, telegram_username, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
            INSERT INTO players (full_name, username, telegram_username, user_id)
            VALUES ($1,$2,$3,$4)
            """, full_name, username, telegram_username, user_id)

    async def get_player_by_user_id(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM players WHERE user_id=$1",
                user_id
            )

    async def get_all_players(self, paid_only=False):
        async with self.pool.acquire() as conn:

            if paid_only:
                return await conn.fetch(
                    "SELECT * FROM players WHERE payment_status=TRUE ORDER BY id"
                )

            return await conn.fetch(
                "SELECT * FROM players ORDER BY id"
            )

    async def delete_player(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM players WHERE user_id=$1",
                user_id
            )

    # 🧹 TURNIRNI TOZALASH
    async def delete_all_players(self):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM players"
            )

    # ================= PAYMENT =================

    async def update_payment_status(self, user_id, photo_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE players SET payment_photo=$1 WHERE user_id=$2",
                photo_id, user_id
            )

    async def confirm_payment(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE players SET payment_status=TRUE WHERE user_id=$1",
                user_id
            )

    # ❌ TO'LOVNI RAD ETISH
    async def reject_payment(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE players
                SET payment_photo=NULL
                WHERE user_id=$1
                """,
                user_id
            )

    # ⏳ KUTILAYOTGAN TO'LOVLAR
    async def get_pending_payments(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
            SELECT * FROM players
            WHERE payment_status=FALSE
            AND payment_photo IS NOT NULL
            ORDER BY id
            """)

    # ================= STATISTICS =================

    async def get_statistics(self):
        async with self.pool.acquire() as conn:

            total = await conn.fetchval(
                "SELECT COUNT(*) FROM players"
            )

            paid = await conn.fetchval(
                "SELECT COUNT(*) FROM players WHERE payment_status=TRUE"
            )

            waiting = await conn.fetchval("""
            SELECT COUNT(*) FROM players
            WHERE payment_status=FALSE
            AND payment_photo IS NOT NULL
            """)

            return total, paid, waiting

    async def close(self):
        if self.pool:
            await self.pool.close()


db = Database()