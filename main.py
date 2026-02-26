import logging
import random
import time
import json
import os
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_TAG = "༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻"
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- بيانات الألعاب (50 سؤال لكل فئة) ---
GAMES_DATA = {
    "اسئله": [("ما هي عاصمة الأردن؟", "عمان"), ("من هو كليم الله؟", "موسى")] * 25,
    "ترتيب": [("ي س م ي", "ميسي"), ("ن د ر ا أ", "الأردن")] * 25,
    "كلمات": [("برمجة", "برمجة"), ("دينار", "دينار")] * 25,
    "المختلف": [("تفاح، موز، أسد، عنب", "أسد"), ("سيارة، باص، دراجة، خبز", "خبز")] * 25,
    "انجليزي": [("معنى Apple؟", "تفاح"), ("معنى Book؟", "كتاب")] * 25,
    "الانديه": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة")] * 25,
    "دينية": [("أول مؤذن في الإسلام؟", "بلال"), ("سورة تعدل ثلث القرآن؟", "الإخلاص")] * 25,
    "اعلام": [("🇯🇴", "الاردن"), ("🇸🇦", "السعودية")] * 25,
}

async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 500000000 if user_id == OWNER_ID else 10000
        u_data = {'id': user_id, 'name': user_name, 'balance': balance, 'points': 0, 'roulette_wins': 0}
        db.insert(u_data)
    return u_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = await get_user_data(update, context)

    # --- [1] أوامر البنك والوظائف المطلوبة (بالدينار) ---
    cmd_map = {
        "راتب": (500, 1500, "استلمت راتبك"),
        "زرف": (-200, 600, "عملية زرف"),
        "كنز": (2000, 5000, "لقيت كنز"),
        "بخشيش": (100, 300, "أخذت بخشيش"),
        "حظ": (-500, 1000, "حظك اليوم"),
        "استثمار": (-1000, 3000, "نتائج استثمارك")
    }

    if text in cmd_map:
        min_v, max_v, msg = cmd_map[text]
        amt = random.randint(min_v, max_v)
        db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        status = "✨ ربحت" if amt > 0 else "📉 خسرت"
        await update.message.reply_text(f"🏦 **إشعار بنكي ملكي**\n━━━━━━━━━━━━━━\n🕹 {msg}: {status} {abs(amt)} دينار أردني\n💰 رصيدك: {u_data['balance'] + amt:,} دينار")

    elif text == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار أردني")

    # --- [2] المطور الأساسي ---
    elif text == "المطور":
        await update.message.reply_text(f"👑 المطور الأساسي والمالك لهذا الصرح:\n\n✨ {OWNER_TAG} ✨")

    # --- [3] ألعاب التحدي ---
    if text in GAMES_DATA:
        q, a = random.choice(GAMES_DATA[text])
        context.chat_data['active_game_ans'] = a
        await update.message.reply_text(f"🎮 تحدي {text}:\n\nالسؤال: 【 {q} 】\n\n(يربح الفائز 500 دينار)")
        return

    if context.chat_data.get('active_game_ans') == text:
        context.chat_data['active_game_ans'] = None
        db.update({'balance': u_data['balance'] + 500}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو {user_name}! إجابتك صح وفزت بـ 500 دينار!")

    # --- [4] الروليت الملكي (المحفوظ مع الإصلاح) ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 اكتب (انا) للمشاركة 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == user_id for p in context.chat_data['r_players']):
            context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
            await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
            players = context.chat_data.get('r_players', [])
            if players:
                winner = random.choice(players)
                w_db = db.get(User.id == winner['id'])
                new_w = w_db.get('roulette_wins', 0) + 1
                db.update({'roulette_wins': new_w, 'balance': w_db['balance'] + 1000}, User.id == winner['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {winner['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} ) والجائزة 1000 دينار!")
            context.chat_data['r_on'] = False

    elif text == "توب الروليت":
        top = sorted(db.all(), key=lambda x: x.get('roulette_wins', 0), reverse=True)[:10]
        msg = "🏆 **قائمة أساطير الروليت:**\n\n"
        for i, u in enumerate(top):
            if u.get('roulette_wins', 0) > 0:
                msg += f"{i+1}- \" {u['name']} \" 🎖 الفوز: {u['roulette_wins']}\n"
        await update.message.reply_text(msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
