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

# --- بنك الألعاب الضخم ---
GAMES_DATA = {
    "اسئله": [("ما هي عاصمة الأردن؟", "عمان"), ("من هو مؤسس الدولة الأموية؟", "معاوية بن أبي سفيان")],
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي"), ("ب ر ش ل و ن ة", "برشلونة")],
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: إمبراطورية", "إمبراطورية")],
    "المختلف": [("تفاح، موز، بطاطس، فراولة (ما المختلف؟)", "بطاطس")],
    "تفكيك": [("مملكة", "م م ل ك ة"), ("عمان", "ع م ا ن")],
    "عكس": [("سماء", "اءمس"), ("قهوة", "ةوهق")],
    "ضد": [("طويل", "قصير"), ("غني", "فقير")],
    "مفرد": [("كتب", "كتاب"), ("أشجار", "شجرة")],
    "عربي": [("جمع كلمة (رجل)", "رجال"), ("مفرد كلمة (أطفال)", "طفل")],
    "انجليزي": [("معنى Car", "سيارة"), ("معنى Book", "كتاب")],
    "اعلام": [("🇯🇴", "الأردن"), ("🇸🇦", "السعودية"), ("🇵🇸", "فلسطين")],
    "عواصم": [("فرنسا", "باريس"), ("مصر", "القاهرة")],
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة")],
    "سيارات": [("شعار الحصان؟", "فيراري"), ("شعار الـ 4 حلقات؟", "اودي")],
    "دين": [("أول مؤذن في الإسلام؟", "بلال بن رباح"), ("عدد سجدات القرآن؟", "15")],
    "ثقافه": [("أكبر محيط في العالم؟", "الهادي"), ("مخترع المصباح؟", "اديسون")]
}

async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = db.get(User.id == user_id)
    if not u_data:
        is_owner = (user_id == OWNER_ID)
        balance = 1000000000000 if is_owner else 10000000000
        u_data = {
            'id': user_id, 'name': user_name, 'balance': balance, 
            'points': 0, 'roulette_wins': 0, 'last_salary': 0, 'last_rob': 0
        }
        db.insert(u_data)
    return u_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    parts = text.split()
    cmd = parts[0]
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    curr_time = time.time()
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return
    u_data = await get_user_data(update, context)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- [1] أوامر البنك الكاملة (العملة: دينار) ---
    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")

    elif cmd == "راتب":
        if curr_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق")

    elif cmd == "زرف":
        if curr_time - u_data.get('last_rob', 0) > 300:
            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 1000000]
            if others:
                target = random.choice(others)
                amt = random.randint(100000, 5000000)
                db.update({'balance': u_data['balance'] + amt, 'last_rob': curr_time}, User.id == user_id)
                db.update({'balance': target['balance'] - amt}, User.id == target['id'])
                await update.message.reply_text(f"🥷 زرفت {amt:,} دينار من {target['name']}")
        else: await update.message.reply_text("⏳ الزرف كل 5 دقائق")

    elif cmd == "كنز":
        amt = random.randint(50000000, 100000000)
        db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        await update.message.reply_text(f"💎 كفو! لقيت كنز فيه {amt:,} دينار")

    elif cmd == "حظ":
        amt = random.randint(1000000, 50000000)
        if random.random() > 0.5:
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            await update.message.reply_text(f"🍀 حظك نار! كسبت {amt:,} دينار")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == user_id)
            await update.message.reply_text(f"💀 حظك سيء.. خسرت {amt:,} دينار")

    elif cmd == "بخشيش":
        amt = random.randint(500000, 2000000)
        db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        await update.message.reply_text(f"☕ بخشيش من البنك: {amt:,} دينار")

    elif cmd == "استثمار":
        profit = random.randint(-50000000, 100000000)
        db.update({'balance': u_data['balance'] + profit}, User.id == user_id)
        await update.message.reply_text(f"📈 نتيجة الاستثمار: {profit:,} دينار")

    elif cmd == "مضاربة":
        amt = random.randint(5000000, 20000000)
        res = random.choice([amt, -amt])
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"⚔️ نتيجة المضاربة: {res:,} دينار")

    elif cmd == "هدية" and len(parts) > 1 and update.message.reply_to_message:
        try:
            amt = int(parts[1])
            t_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= amt > 0:
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                t_data = db.get(User.id == t_id)
                db.update({'balance': t_data['balance'] + amt}, User.id == t_id)
                await update.message.reply_text(f"🎁 تم إرسال {amt:,} دينار هدية")
        except: pass

    # --- [2] الألعاب ---
    if cmd in GAMES_DATA:
        q, a = random.choice(GAMES_DATA[cmd])
        context.chat_data['game_ans'] = a
        await update.message.reply_text(f"🎮 لعبة {cmd}:\nالسؤال: 【 {q} 】\n(الجائزة: 10 مليون)")
        return

    if cmd == "تخمين":
        num = random.randint(1, 10)
        context.chat_data['guess_num'] = str(num)
        await update.message.reply_text("🎲 خمن الرقم من 1 لـ 10")
        return

    if cmd == "اضف" and parts[1] == "تخمين" and len(parts) > 2:
        context.chat_data['guess_num'] = parts[2]
        await update.message.reply_text(f"✅ تم وضع الرقم التخميني بواسطة {user_name}")
        return

    if context.chat_data.get('game_ans') and text.lower() == context.chat_data.get('game_ans').lower():
        context.chat_data['game_ans'] = None
        db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو {user_name}! إجابة صح وفزت بـ 10,000,000 دينار!")

    if context.chat_data.get('guess_num') and text == context.chat_data.get('guess_num'):
        context.chat_data['guess_num'] = None
        db.update({'balance': u_data['balance'] + 5000000}, User.id == user_id)
        await update.message.reply_text(f"🎯 صح! التخمين كان {text} وفزت بـ 5 مليون دينار!")

    # --- [3] الروليت الملكي ---
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
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = w_db.get('roulette_wins', 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑\n\n       🔥🔥 \"{new_w} نقاط\"🔥🔥")
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id = u['id'])
            context.chat_data['r_on'] = False

    elif text == "توب الروليت":
        top = sorted(db.all(), key=lambda x: x.get('roulette_wins', 0), reverse=True)[:10]
        msg = "🏆 **قائمة أساطير الروليت:**\n\n"
        icons = ["1- 👑", "2- 🔥", "3- ♥️", "4- 🌟", "5- ✨", "6- 💎", "7- 🎖", "8- 🏅", "9- 🎗", "10- 🦾"]
        found = False
        for i, u in enumerate(top):
            if u.get('roulette_wins', 0) > 0:
                msg += f"{icons[i]} \" {u['name']} \" + ( {u['roulette_wins']} )\n"
                found = True
        await update.message.reply_text(msg if found else "لا توجد نقاط.")

    # --- [4] ملك التفاعل والمطور ---
    elif text == "ملك التفاعل":
        all_u = db.all()
        if all_u:
            win = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    elif text == "المطور":
        await update.message.reply_text(f"🛠 المطور والمالك الأساسي:\n{OWNER_NAME}")

    elif text == "العاب":
        await update.message.reply_text(f"👑 **بوابـة ألعـاب {OWNER_NAME}** 👑\n\n💰 **البنك:** (رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية)\n🧩 **المسابقات:** (اسئله، تخمين، ترتيب، كلمات، المختلف، تففكيك، عكس، ضد، مفرد، عربي، اعلام، عواصم، اندية، سيارات)\n🎲 **التفاعل:** (روليت، توب الروليت، ملك التفاعل)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
