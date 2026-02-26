import logging
import random
import time
import asyncio
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

# --- بنك الأسئلة الشامل ---
GAMES_DATA = {
    "اسئله": [("عاصمة الأردن؟", "عمان"), ("أصغر قارة؟", "استراليا")],
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي")],
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية")],
    "المختلف": [("تفاح، موز، جزر، عنب", "جزر")],
    "تفكيك": [("مملكة", "م م ل ك ة")],
    "عكس": [("سماء", "اءمس")],
    "ضد": [("قوي", "ضعيف")],
    "مفرد": [("أقلام", "قلم")],
    "عربي": [("جمع (بحر)", "بحار")],
    "انجليزي": [("معنى Pen", "قلم")],
    "اعلام": [("🇯🇴", "الأردن"), ("🇵🇸", "فلسطين")],
    "عواصم": [("اليابان", "طوكيو")],
    "اندية": [("نادي ليفربول في أي دولة؟", "انجلترا")],
    "سيارات": [("شعار الـ T؟", "تويوتا")]
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {'id': user_id, 'name': user_name, 'balance': balance, 'points': 0, 'roulette_wins': 0, 'last_salary': 0}
        db.insert(u_data)
    return u_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    parts = text.split()
    cmd = parts[0]
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return
    u_data = await get_user_data(update)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- [1] أوامر البنك (دينار) ---
    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")

    elif cmd == "راتب":
        curr = time.time()
        if curr - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr}, User.id == user_id)
            await update.message.reply_text(f"💵 تم إيداع راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")

    elif cmd == "زرف":
        others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 1000000]
        if others:
            target = random.choice(others)
            amt = random.randint(500000, 5000000)
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            db.update({'balance': target['balance'] - amt}, User.id == target['id'])
            await update.message.reply_text(f"🥷 زرفت {amt:,} دينار من {target['name']}")

    elif cmd == "حظ":
        amt = random.randint(1000000, 20000000)
        if random.random() > 0.5:
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            await update.message.reply_text(f"🍀 كسبت {amt:,} دينار!")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == user_id)
            await update.message.reply_text(f"💀 خسرت {amt:,} دينار")

    elif cmd == "هدية" and update.message.reply_to_message:
        try:
            amt = int(parts[1])
            t_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= amt > 0:
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                t_data = db.get(User.id == t_id)
                db.update({'balance': (t_data['balance'] if t_data else 0) + amt}, User.id == t_id)
                await update.message.reply_text(f"🎁 أرسلت {amt:,} دينار هدية!")
        except: pass

    # --- [2] الألعاب الحماسية الجديدة ---
    elif cmd == "قنبلة":
        context.chat_data['bomb_on'] = True
        context.chat_data['bomb_user'] = user_id
        await update.message.reply_text("💣 بدأت القنبلة! الأسرع يكتب 'فك' ليمررها لغيره!\nالمؤقت: 20 ثانية")
        await asyncio.sleep(20)
        if context.chat_data.get('bomb_on'):
            loser_id = context.chat_data['bomb_user']
            loser_data = db.get(User.id == loser_id)
            db.update({'balance': max(0, loser_data['balance'] - 500000000)}, User.id == loser_id)
            await update.message.reply_text(f"💥 بوم! انفجرت في {loser_data['name']} وخسر 500 مليون!")
            context.chat_data['bomb_on'] = False

    elif text == "فك" and context.chat_data.get('bomb_on'):
        context.chat_data['bomb_user'] = user_id
        await update.message.reply_text(f"🏃 مررت القنبلة! هي الآن عند: {user_name}")

    elif cmd == "مزاد" and len(parts) > 1:
        bid = int(parts[1])
        if u_data['balance'] >= bid:
            context.chat_data['top_bid'] = bid
            context.chat_data['top_bidder'] = user_name
            await update.message.reply_text(f"🔨 مزاد جديد من {user_name} بمبلغ {bid:,} دينار!")

    elif cmd == "صيد":
        target_num = random.randint(1000, 9999)
        context.chat_data['hunt_num'] = str(target_num)
        await update.message.reply_text(f"🎯 اصطاد الرقم التالي بأسرع وقت: `{target_num}`")

    elif cmd == "حرب":
        await update.message.reply_text("⚔️ بدأت حرب العصابات! الفريق الذي يجمع 'نقاط تفاعل' أكثر خلال دقيقتين يربح مليار دينار!")

    # --- [3] نظام المسابقات التقليدي ---
    if cmd in GAMES_DATA:
        q, a = random.choice(GAMES_DATA[cmd])
        context.chat_data['game_ans'] = a
        await update.message.reply_text(f"🎮 {cmd}: {q}")
        return

    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None
        db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ صح يا {user_name}! فزت بـ 10 مليون دينار!")

    if context.chat_data.get('hunt_num') and text == context.chat_data['hunt_num']:
        context.chat_data['hunt_num'] = None
        db.update({'balance': u_data['balance'] + 50000000}, User.id == user_id)
        await update.message.reply_text(f"🎯 قناص! صيد موفق وفزت بـ 50 مليون دينار!")

    # --- [4] الروليت والرسائل الملكية ---
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
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )")
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑")
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    elif text == "ملك التفاعل":
        all_u = db.all()
        if all_u:
            win = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    elif text == "المطور":
        await update.message.reply_text(f"🛠 المالك الأساسي:\n{OWNER_NAME}")

    elif text == "العاب":
        await update.message.reply_text(f"👑 **بوابـة ألعـاب {OWNER_NAME}** 👑\n\n💰 **البنك:** (رصيدي، راتب، زرف، حظ، هدية)\n🧩 **المسابقات:** (قنبلة، صيد، مزاد، حرب، اسئله، ترتيب، تفكيك، عكس، اعلام...)\n🎲 **التفاعل:** (روليت، ملك التفاعل)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__':
    main()
