# config.py
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🇳🇦🇸 ♛༒۝༻"

def get_rank_name(level):
    if level < 10: return "🆕 عضو جديد"
    if level < 50: return "🥉 برونزي"
    if level < 150: return "🥇 ذهبي"
    return "👑 ملك التفاعل"
