from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_ID

class ChannelPost:
    """Kanalga post yuborish uchun yordamchi klass"""
    
    def __init__(self, bot):
        self.bot = bot
        self.last_post_id = None
    
    async def send_players_list(self, players, with_button=True):
        """
        Ishtirokchilar ro'yxatini kanalga yuborish
        
        Args:
            players: Ishtirokchilar ro'yxati
            with_button: Ro'yxatdan o'tish tugmasi qo'shilsinmi?
        
        Returns:
            int: Yuborilgan xabarning ID si
        """
        # Ro'yxat matnini tayyorlash
        if not players:
            text = "━━━━━━━━━━━━━━━━━━\n"
            text += "📋 TURNIR RO'YXATI\n"
            text += "━━━━━━━━━━━━━━━━━━\n\n"
            text += "Hali hech kim ro'yxatdan o'tmagan.\n"
            text += "━━━━━━━━━━━━━━━━━━"
        else:
            text = "━━━━━━━━━━━━━━━━━━\n"
            text += "📋 TURNIR RO'YXATI\n"
            text += "━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, player in enumerate(players, 1):
                text += f"{i}. {player['full_name']}\n"
            
            text += "\n━━━━━━━━━━━━━━━━━━"
        
        # Tugma qo'shish
        if with_button:
            register_btn = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Turnirga ro'yxatdan o'tish", callback_data="register")]
                ]
            )
            msg = await self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                reply_markup=register_btn
            )
        else:
            msg = await self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text
            )
        
        self.last_post_id = msg.message_id
        return msg.message_id
    
    async def update_players_list(self, players, with_button=True):
        """
        Kanaldagi ro'yxatni yangilash (eski postni o'chirib, yangisini yozish)
        
        Args:
            players: Ishtirokchilar ro'yxati
            with_button: Ro'yxatdan o'tish tugmasi qo'shilsinmi?
        """
        # Avvalgi postni o'chirish
        if self.last_post_id:
            try:
                await self.bot.delete_message(
                    chat_id=CHANNEL_ID,
                    message_id=self.last_post_id
                )
            except:
                pass  # Xatolik bo'lsa davom et
        
        # Yangi post yuborish
        await self.send_players_list(players, with_button)
    
    async def send_tournament_start(self, players_count):
        """
        Turnir boshlanganligi haqida xabar yuborish
        """
        text = f"""
━━━━━━━━━━━━━━━━━━
🎮 TURNIR BOSHLANDI! ⚽️
━━━━━━━━━━━━━━━━━━

👥 Ishtirokchilar soni: {players_count}

⚔️ Matchlar jadvali tez kunda e'lon qilinadi.
📢 Barcha ishtirokchilarga omad! 🍀
━━━━━━━━━━━━━━━━━━
"""
        msg = await self.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )
        return msg.message_id
    
    async def send_match_results(self, match, player1, player2):
        """
        Match natijalarini kanalga yuborish
        """
        winner = player1 if match['winner_id'] == player1['id'] else player2
        
        text = f"""
━━━━━━━━━━━━━━━━━━
⚽️ MATCH NATIJASI
━━━━━━━━━━━━━━━━━━

🎮 {player1['full_name']} vs {player2['full_name']}
📊 Hisob: {match['score']}
🏆 G'olib: {winner['full_name']}

✅ Match yakunlandi!
━━━━━━━━━━━━━━━━━━
"""
        await self.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )
    
    async def send_tournament_results(self, winner):
        """
        Turnir yakunlari
        """
        text = f"""
━━━━━━━━━━━━━━━━━━
🏆 TURNIR YAKUNLANDI! 🏆
━━━━━━━━━━━━━━━━━━

🥇 1-o'rin: {winner['full_name']}
🎉 G'olibni tabriklaymiz!

Barcha ishtirokchilarga rahmat!
━━━━━━━━━━━━━━━━━━
"""
        await self.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )
    
    async def send_announcement(self, text):
        """
        E'lon yuborish
        """
        await self.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )

# Global kanal post obyekti (bot ishga tushganda yaratiladi)
channel_post = None

def init_channel_post(bot):
    """Kanal post obyektini yaratish"""
    global channel_post
    channel_post = ChannelPost(bot)
    return channel_post
