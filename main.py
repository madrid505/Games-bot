import logging
import random
import time
import json
import os
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات الملكية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻" 
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- بنك الأسئلة ---
GAMES_DATA = {
    "اسئله": [("ما هي عاصمة السعودية؟", "الرياض"), ("من هو خاتم الأنبياء؟", "محمد"), ("كم عدد قارات العالم؟", "7")],
    "دين": [("من هو أول من أسلم من الرجال؟", "أبو بكر الصديق"), ("ما هي أطول سورة في القرآن؟", "البقرة"), ("كم عدد الرسل في القرآن؟", "25")],
    "ثقافه": [("ما هو أسرع حيوان بري؟", "الفهد"), ("أين يوجد برج إيفل؟", "باريس"), ("كم قلب للأخطبوط؟", "3")],
    "انجليزي": [("معنى Apple؟", "تفاح"), ("عكس Hot؟", "Cold"), ("كلمة School؟", "مدرسة")],
    "رياضيات": [("5 + 7 * 2", "19"), ("100 / 4", "25"), ("9 * 9", "81")],
    "حزوره": [("يسير بلا أرجل ويدخل الأذنين؟", "الصوت"), ("له أسنان ولا يعض؟", "المشط")]
}

async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_data = db.get(User.id == user_id)
    if not user_data:
        is_owner = (user_id == OWNER_ID)
        balance = 1000000000000 if is_owner else 10000000000
        user_data = {'id': user_id, 'name': user_name, 'balance': balance, 'points': 0, 'roulette_wins': 0}
        db.insert(user_data)
    return user_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    parts = text.split()
    cmd = parts[0]
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return
    u_data = await get_user_data(update, context)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- [1] أوامر البنك ---
    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} ريال")

    elif cmd == "بخشيش":
        amt = random.randint(500000, 2000000)
        db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        await update.message.reply_text(f"☕ تفضل بخشيش من البنك: {amt:,} ريال")

    elif cmd == "حظ":
        amt = random.randint(1000000, 50000000)
        if random.random() > 0.5:
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            await update.message.reply_text(f"🍀 حظك نار! كسبت {amt:,} ريال")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == user_id)
            await update.message.reply_text(f"💀 حظك سيء.. خسرت {amt:,} ريال")

    elif cmd == "استثمار":
        profit = random.randint(-50000000, 100000000)
        db.update({'balance': u_data['balance'] + profit}, User.id == user_id)
        msg = f"📈 نجح الاستثمار وربحت {profit:,} ريال!" if profit > 0 else f"📉 فشل الاستثمار وخسرت {abs(profit):,} ريال"
        await update.message.reply_text(msg)

    elif cmd == "مضاربة":
        amt = random.randint(5000000, 20000000)
        if random.choice([True, False]):
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            await update.message.reply_text(f"⚔️ كسبت في المضاربة: {amt:,} ريال")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == user_id)
            await update.message.reply_text(f"🤕 خسرت في المضاربة: {amt:,} ريال")

    # --- [2] الألعاب ---
    if cmd in GAMES_DATA:
        q, a = random.choice(GAMES_DATA[cmd])
        context.chat_data['game_ans'] = a
        await update.message.reply_text(f"🎮 لعبة {cmd}:\nالسؤال: 【 {q} 】\n(الجائزة: 10 مليون)")
        return

    if context.chat_data.get('game_ans') and text.lower() == context.chat_data.get('game_ans').lower():
        context.chat_data['game_ans'] = None
        db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو {user_name}! إجابة صح وفزت بـ 10,000,000 ريال!")

    # --- [3] الروليت (الرسائل الملكية الأصلية) ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
            players = context.chat_data.get('r_players', [])
            if players:
                winner_raw = random.choice(players)
                w_id = winner_raw['id']
                w_db = db.get(User.id == w_id)
                new_w = w_db.get('roulette_wins', 0) + 1
                db.update({'roulette_wins': new_w}, User.id = w_id)
                
                # رسالة الفوز بالجولة الأصلية
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {winner_raw['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                
                # إعلان ملك الروليت عند 5 نقاط
                if new_w >= 5:
                    final_msg = (f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {winner_raw['name']} \" 👑\n\n       🔥🔥 \"{new_w} نقاط\"🔥🔥")
                    await update.message.reply_text(final_msg)
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    elif text == "توب الروليت":
        top = sorted(db.all(), key=lambda x: x.get('roulette_wins', 0), reverse=True)[:10]
        msg = "🏆 **قائمة أساطير الروليت:**\n\n"
        icons = ["1- 👑", "2- 🔥", "3- ♥️", "4- 🌟", "5- ✨", "6- 💎", "7- 🎖", "8- 🏅", "9- 🎗", "10- 🦾"]
        for i, u in enumerate(top):
            if u.get('roulette_wins', 0) > 0:
                msg += f"{icons[i]} \" {u['name']} \" + ( {u['roulette_wins']} )\n"
        await update.message.reply_text(msg if "1-" in msg else "لا توجد نقاط مسجلة بعد.")

    # --- [4] ملك التفاعل (الرسالة الملكية الأصلية) ---
    elif text == "ملك التفاعل" and (user_id == OWNER_ID or True): # السماح للكل مؤقتاً للتجربة
        all_users = db.all()
        if all_users:
            winner = max(all_users, key=lambda x: x.get('points', 0))
            msg = (f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {winner['name']}\n\nعدد النقاط : {winner['points']}\n\nID : {winner['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            await update.message.reply_text(msg)
            for u in all_users: db.update({'points': 0}, User.id == u['id'])

    elif text == "المطور":
        await update.message.reply_text(f"🛠 المطور والمالك الأساسي:\n{OWNER_NAME}")

    elif text == "العاب":
        menu = (f"👑 **بوابـة ألعـاب {OWNER_NAME}** 👑\n\n💰 **البنك:** (رصيدي، حظ، بخشيش، استثمار، مضاربة)\n🧩 **المسابقات:** (دين، ثقافه، انجليزي، رياضيات، اسئله، حزوره)\n🎲 **التفاعل:** (روليت، توب الروليت، ملك التفاعل)")
        await update.message.reply_text(menu, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
