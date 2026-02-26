# config.py - الإعدادات الأساسية فقط
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🇳🇦🇸 ♛༒۝༻"

# نظام الرتب (لقب العضو بناءً على مستواه)
def get_rank_name(level):
    if level < 10: return "🆕 عضو جديد"
    if level < 30: return "🥉 برونزي"
    if level < 60: return "🥈 فضي"
    if level < 100: return "🥇 ذهبي"
    if level < 150: return "💎 ماسي"
    return "👑 ملك التفاعل"
