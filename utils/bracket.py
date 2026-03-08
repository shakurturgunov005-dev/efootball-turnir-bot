import math

def create_bracket(players):
    n = len(players)
    if n < 2:
        return "🏆 TURNIR JADVALI 🏆\n\nTurnir uchun yetarli ishtirokchi yo'q (kamida 2 ta bo'lishi kerak)."
    size = 2 ** math.ceil(math.log2(n))
    bracket = "🏆 TURNIR JADVALI 🏆\n" + "═" * 40 + "\n\n"
    rounds = int(math.log2(size))
    for round_num in range(rounds, 0, -1):
        round_name = get_round_name(round_num, rounds)
        bracket += f"\n⚔️ {round_name} ⚔️\n" + "─" * 40 + "\n"
        matches_in_round = size // (2 ** (rounds - round_num + 1))
        for match_idx in range(matches_in_round):
            p1 = players[match_idx*2]['full_name'] if match_idx*2 < n else "🔵 BYE (tugallanmagan)"
            p2 = players[match_idx*2+1]['full_name'] if match_idx*2+1 < n else "🔵 BYE (tugallanmagan)"
            bracket += f"⚽️ {p1[:20]:<20} vs {p2[:20]:<20}\n"
    bracket += "\n" + "═" * 40 + "\n"
    bracket += f"👥 Jami ishtirokchilar: {n} | 🏆 G'olib: aniqlanmagan"
    return bracket

def get_round_name(round_num, total_rounds):
    if round_num == total_rounds:
        return "🏁 FINAL"
    elif round_num == total_rounds - 1:
        return "🥉 YARIM FINAL"
    elif round_num == total_rounds - 2:
        return "🏅 CHORAK FINAL"
    else:
        return f"⚔️ 1/{2**(total_rounds - round_num + 1)} FINAL"

def create_match_schedule(players, matches):
    if not matches:
        return "⚽️ Hali matchlar yaratilmagan."
    schedule = "⚽️ MATCHLAR JADVALI ⚽️\n" + "═" * 50 + "\n\n"
    for match in matches:
        p1 = p2 = "Noma'lum"
        for p in players:
            if p['id'] == match['player1_id']:
                p1 = p['full_name']
            if p['id'] == match['player2_id']:
                p2 = p['full_name']
        match_time = match['match_time'].strftime("%d.%m.%Y %H:%M") if match['match_time'] else "Vaqt belgilanmagan"
        score = match['score'] if match['score'] else "— : —"
        status = "✅" if match['status'] == 'completed' else "⏳"
        schedule += f"{status} {p1} vs {p2}\n   🕐 {match_time}\n   📊 Hisob: {score}\n\n"
    return schedule

def get_winner_bracket(players, matches):
    winners = []
    for match in matches:
        if match['winner_id']:
            for p in players:
                if p['id'] == match['winner_id']:
                    winners.append(p['full_name'])
                    break
    if not winners:
        return "🏆 Hali g'oliblar aniqlanmagan."
    result = "🏆 G'OLIBLAR 🏆\n" + "═" * 30 + "\n\n"
    for i, winner in enumerate(winners, 1):
        result += f"{i}. {winner}\n"
    return result