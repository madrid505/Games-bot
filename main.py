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

# --- بنك البيانات الضخم ---
GAMES_DATA = {
    "اسئله": [("عاصمة الأردن؟", "عمان"), ("أطول نهر؟", "النيل")],
    "دين": [("أول من أسلم من الرجال؟", "أبو بكر الصديق"), ("أطول سورة؟", "البقرة")],
    "ثقافه": [("أسرع حيوان بري؟", "الفهد"), ("أين يوجد برج إيفل؟", "باريس")],
    "انجليزي": [("معنى Apple؟", "تفاح"), ("معنى School؟", "مدرسة")],
    "رياضيات": [("5 + 7 * 2", "19"), ("100 / 4", "25")],
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي")],
    "تفكيك": [("مدرسة", "م د ر س ة")],
    "عكس": [("قمر", "رمق")],
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية")],
    "اعلام": [("🇯🇴", "الأردن"), ("🇸🇦", "السعودية")],
    "عواصم": [("فرنسا", "باريس"), ("مصر", "القاهرة")],
    "اندية": [("نادي الملكي؟", "ريال مدريد")],
    "سيارات": [("شعار الحصان؟", "فيراري")]
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {'id': user_id, 'name': user_name, 'balance': balance, 'points': 0, 'roulette_wins': 0, 'last_salary': 0, 'last_rob': 0}
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
    u_data = await get_user_data(update)
    
    # زيادة نقاط التفاعل
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- [1] أوامر البنك الكاملة (دينار) ---
    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")

    elif cmd == "راتب":
        wait = 0 if context.chat_data.get('lucky_hour') else 600
        if curr_time - u_data.get('last_salary', 0) > wait:
            multiplier = 10 if context.chat_data.get('lucky_hour') else 1
            amt = random.randint(5000000, 15000000) * multiplier
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr_time}, User.id == user_id)
            msg = f"💵 استلمت راتب مضاعف: {amt:,} دينار!" if multiplier > 1 else f"💵 تم إيداع راتبك: {amt:,} دينار"
            await update.message.reply_text(msg)
        else: await update.message.reply_text(f"⏳ انتظر {int((wait - (curr_time - u_data['last_salary']))/60)} دقيقة")

    elif cmd == "زرف":
        wait = 0 if context.chat_data.get('lucky_hour') else 300
        if curr_time - u_data.get('last_rob', 0) > wait:
            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 1000000]
            if others:
                target = random.choice(others)
                amt = random.randint(1000000, 10000000)
                db.update({'balance': u_data['balance'] + amt, 'last_rob': curr_time}, User.id == user_id)
                db.update({'balance': max(0, target['balance'] - amt)}, User.id == target['id'])
                await update.message.reply_text(f"🥷 زرفت {amt:,} دينار من {target['name']}!")
        else: await update.message.reply_text("⏳ الزرف كل 5 دقائق (إلا في ساعة الحظ)")

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
        await update.message.reply_text(f"☕ تفضل بخشيش: {amt:,} دينار")

    elif cmd == "استثمار":
        profit = random.randint(-50000000, 100000000)
        db.update({'balance': u_data['balance'] + profit}, User.id == user_id)
        await update.message.reply_text(f"📈 نتيجة الاستثمار: {profit:,} دينار")

    elif cmd == "مضاربة":
        amt = random.randint(5000000, 30000000)
        res = random.choice([amt, -amt])
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"⚔️ نتيجة المضاربة: {res:,} دينار")

    elif cmd == "هدية" and update.message.reply_to_message and len(parts) > 1:
        try:
            amt = int(parts[1])
            t_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= amt > 0:
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                t_data = db.get(User.id == t_id)
                db.update({'balance': (t_data['balance'] if t_data else 0) + amt}, User.id == t_id)
                await update.message.reply_text(f"🎁 تم إرسال {amt:,} دينار هدية!")
        except: pass

    # --- [2] الألعاب الحماسية والموسعة ---
    if cmd == "قنبلة":
        context.chat_data['bomb_on'], context.chat_data['bomb_user'] = True, user_id
        await update.message.reply_text("💣 القنبلة بدأت! اكتب 'فك' لتمريها.. المؤقت 20 ثانية")
        await asyncio.sleep(20)
        if context.chat_data.get('bomb_on'):
            loser = db.get(User.id == context.chat_data['bomb_user'])
            db.update({'balance': max(0, loser['balance'] - 500000000)}, User.id == loser['id'])
            await update.message.reply_text(f"💥 بوم! انفجرت في {loser['name']} وخسر 500 مليون!")
            context.chat_data['bomb_on'] = False

    elif text == "فك" and context.chat_data.get('bomb_on'):
        context.chat_data['bomb_user'] = user_id
        await update.message.reply_text(f"🏃 مررتها! هي الآن عند: {user_name}")

    elif cmd == "مزاد" and len(parts) > 1:
        bid = int(parts[1])
        if u_data['balance'] >= bid:
            context.chat_data['top_bid'] = bid
            context.chat_data['top_bidder'] = user_name
            await update.message.reply_text(f"🔨 {user_name} رفع المزاد لـ {bid:,} دينار!")

    elif cmd == "صيد":
        target = str(random.randint(1000, 9999))
        context.chat_data['hunt'] = target
        await update.message.reply_text(f"🎯 الأسرع يصطاد الرقم: `{target}`")

    elif cmd == "حرب":
        await update.message.reply_text("⚔️ بدأت حرب العصابات! الفريق الأكثر تفاعلاً يربح مليار دينار بعد دقيقتين!")

    elif cmd == "ساعة" and parts[1] == "الحظ":
        if user_id == OWNER_ID:
            context.chat_data['lucky_hour'] = True
            await update.message.reply_text("🎰 اشتعلت! بدأت ساعة الحظ: الرواتب x10 والزرف مفتوح!")
            await asyncio.sleep(600)
            context.chat_data['lucky_hour'] = False
            await update.message.reply_text("🏁 انتهت ساعة الحظ.")

    # --- [3] المسابقات التقليدية ---
    if cmd in GAMES_DATA:
        q, a = random.choice(GAMES_DATA[cmd])
        context.chat_data['game_ans'] = a
        await update.message.reply_text(f"🎮 لعبة {cmd}:\nالسؤال: 【 {q} 】\n(الجائزة: 10 مليون)")
        return

    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None
        db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو {user_name}! صح وفزت بـ 10 مليون دينار!")

    if context.chat_data.get('hunt') and text == context.chat_data['hunt']:
        context.chat_data['hunt'] = None
        db.update({'balance': u_data['balance'] + 50000000}, User.id == user_id)
        await update.message.reply_text(f"🎯 قناص! فزت بـ 50 مليون دينار!")

    # --- [4] الروليت والرسائل الملكية ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == user_id for p in context.chat_data['r_players']):
            context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
            await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
            players = context.chat_data['r_players']
            if players:
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = w_db.get('roulette_wins', 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑\n\n       🔥🔥 \"{new_w} نقاط\"🔥🔥")
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
        await update.message.reply_text(f"👑 **بوابـة ألعـاب {OWNER_NAME}** 👑\n\n💰 **البنك:** (رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية)\n🧩 **المسابقات:** (قنبلة، مزاد، صيد، حرب، ساعة الحظ، اسئلة، دين، ثقافة...)\n🎲 **التفاعل:** (روليت، ملك التفاعل)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
