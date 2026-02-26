# royal.py
import random
from tinydb import TinyDB, Query

db = TinyDB('bank_data.json')
User = Query()

MSG_ROULETTE_START = "🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹"
MSG_ROULETTE_JOIN = "📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢"
MSG_ROULETTE_WIN = "👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {name} \" 👑\n\n🏆 فوزك رقم: ( {wins} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉"
MSG_ROULETTE_KING = "👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {name} \" 👑\n\n       🔥🔥 \"فاز بـ {wins} جولات متتالية\"🔥🔥"

async def get_top_active():
    all_users = db.all()
    if not all_users: return "لا يوجد بيانات."
    top = max(all_users, key=lambda x: x.get('points', 0))
    return f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {top['name']}\n\nنقاطه : {top['points']}\n\n🏆 مباارك يا أسطورة!"

async def process_roulette_winner(players):
    if not players: return None
    winner = random.choice(players)
    u_db = db.get(User.id == winner['id'])
    new_wins = (u_db.get('roulette_wins', 0) if u_db else 0) + 1
    db.update({'roulette_wins': new_wins}, User.id == winner['id'])
    res = {"name": winner['name'], "wins": new_wins, "is_king": (new_wins >= 5)}
    if res["is_king"]:
        for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
    return res
