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
            
            await conn.execute("""
                 CREATE TABLE IF NOT EXISTS standings (
                     player_id INTEGER PRIMARY KEY REFERENCES players(id),
                     played INTEGER DEFAULT 0,
                     wins INTEGER DEFAULT 0,
                     draws INTEGER DEFAULT 0,
                     losses INTEGER DEFAULT 0,
                     goals_for INTEGER DEFAULT 0,
                     goals_against INTEGER DEFAULT 0,
                     goal_diff INTEGER DEFAULT 0,
                     points INTEGER DEFAULT 0
                )
            """)

    async def add_player(self, full_name, username, telegram_username, user_id):
        async with self.pool.acquire() as conn:
            return await conn.execute("""
                INSERT INTO players (full_name, username, telegram_username, user_id) 
                VALUES ($1, $2, $3, $4)
            """, full_name, username, telegram_username, user_id)

    async def get_player_by_user_id(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM players WHERE user_id = $1", user_id)

    async def get_all_players(self, paid_only=False):
        async with self.pool.acquire() as conn:
            if paid_only:
                return await conn.fetch("SELECT * FROM players WHERE payment_status = TRUE ORDER BY id")
            return await conn.fetch("SELECT * FROM players ORDER BY id")

    async def update_payment_status(self, user_id, photo_id=None):
        async with self.pool.acquire() as conn:
            if photo_id:
                await conn.execute("UPDATE players SET payment_photo = $1 WHERE user_id = $2", photo_id, user_id)
            else:
                await conn.execute("UPDATE players SET payment_status = TRUE WHERE user_id = $1", user_id)

    async def delete_player(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM players WHERE user_id = $1", user_id)

    async def get_statistics(self):
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM players")
            paid = await conn.fetchval("SELECT COUNT(*) FROM players WHERE payment_status = TRUE")
            waiting = await conn.fetchval("SELECT COUNT(*) FROM players WHERE payment_status = FALSE AND payment_photo IS NOT NULL")
            return total, paid, waiting

    async def create_match(self, player1_id, player2_id, round_num, match_time):
        async with self.pool.acquire() as conn:
            return await conn.execute("""
                INSERT INTO matches (player1_id, player2_id, round, match_time)
                VALUES ($1, $2, $3, $4)
            """, player1_id, player2_id, round_num, match_time)

    async def update_match_score(self, match_id, score, winner_id):
        async with self.pool.acquire() as conn:
        
            match = await conn.fetchrow(
                "SELECT player1_id, player2_id FROM matches WHERE id=$1",
                match_id
            )

        await conn.execute("""
            UPDATE matches
            SET score = $1, winner_id = $2, status = 'completed'
            WHERE id = $3
        """, score, winner_id, match_id)

    player1_id = match["player1_id"]
    player2_id = match["player2_id"]

    score1, score2 = map(int, score.split(":"))

    await self.update_standings(player1_id, player2_id, score1, score2)

    async def get_matches(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM matches ORDER BY round, id")
    
    async def get_match(self, match_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM matches WHERE id = $1",
                match_id
            )
    
    async def update_standings(self, player1_id, player2_id, score1, score2):
        async with self.pool.acquire() as conn:

            # player1 statistikasi
            await conn.execute("""
                UPDATE standings
                SET
                    played = played + 1,
                    goals_for = goals_for + $1,
                    goals_against = goals_against + $2,
                    goal_diff = goal_diff + ($1 - $2)
                WHERE player_id = $3
            """, score1, score2, player1_id)

            # player2 statistikasi
            await conn.execute("""
                UPDATE standings
                SET
                    played = played + 1,
                    goals_for = goals_for + $1,
                    goals_against = goals_against + $2,
                    goal_diff = goal_diff + ($1 - $2)
                WHERE player_id = $3
            """, score2, score1, player2_id)

            # g‘alaba / durang / mag‘lubiyat
            if score1 > score2:
                await conn.execute("UPDATE standings SET wins = wins + 1, points = points + 3 WHERE player_id = $1", player1_id)
                await conn.execute("UPDATE standings SET losses = losses + 1 WHERE player_id = $1", player2_id)

            elif score2 > score1:
                await conn.execute("UPDATE standings SET wins = wins + 1, points = points + 3 WHERE player_id = $1", player2_id)
                await conn.execute("UPDATE standings SET losses = losses + 1 WHERE player_id = $1", player1_id)

            else:
                await conn.execute("UPDATE standings SET draws = draws + 1, points = points + 1 WHERE player_id = $1", player1_id)
                await conn.execute("UPDATE standings SET draws = draws + 1, points = points + 1 WHERE player_id = $1", player2_id)
                
    async def init_standings(self):
        async with self.pool.acquire() as conn:
            players = await conn.fetch(
                "SELECT id FROM players WHERE payment_status = TRUE"
            )

            for player in players:
                await conn.execute("""
                    INSERT INTO standings (player_id)
                    VALUES ($1)
                    ON CONFLICT (player_id) DO NOTHING
                """, player["id"])
                
    async def close(self):
        if self.pool:
            await self.pool.close()

db = Database()