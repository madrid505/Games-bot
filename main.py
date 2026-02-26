import logging
import random
import time
import asyncio
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

# --- الإعدادات الملكية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻" 
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- بنك الأسئلة الشامل (لا يوجد نقص) ---
GAMES_DATA = {
    "اسئله": [("ما هي عاصمة الأردن؟", "عمان"), ("أطول نهر في العالم؟", "النيل")],
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("كم عدد سجدات القرآن؟", "15")],
    "ثقافه": [("أين يقع تمثال الحرية؟", "نيويورك"), ("مخترع المصباح؟", "اديسون")],
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي"), ("ب ر ش ل و ن ة", "برشلونة")],
    "تفكيك": [("مملكة", "م م ل ك ة"), ("عمان", "ع م ا ن")],
    "عكس": [("سماء", "اءمس"), ("قهوة", "ةوهق")],
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: إمبراطورية", "إمبراطورية")],
    "المختلف": [("تفاح، موز، بطاطس، فراولة", "بطاطس")],
    "ضد": [("طويل", "قصير"), ("غني", "فقير")],
    "مفرد": [("كتب", "كتاب"), ("أشجار", "شجرة")],
    "عربي": [("جمع كلمة (رجل)", "رجال"), ("مفرد كلمة (أطفال)", "طفل")],
    "انجليزي": [("معنى Car", "سيارة"), ("معنى Book", "كتاب")],
    "اعلام": [("🇯🇴", "الأردن"), ("🇸🇦", "السعودية"), ("🇵🇸", "فلسطين")],
    "عواصم": [("فرنسا", "باريس"), ("مصر", "القاهرة")],
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة")],
    "سيارات": [("شعار الحصان؟", "فيراري"), ("شعار الـ 4 حلقات؟", "اودي")],
    "دول": [("أي دولة لغتها الرسمية البرتغالية في أمريكا الجنوبية؟", "البرازيل")]
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'roulette_wins': 0, 'last_salary': 0, 'last_rob': 0}
        db.insert(u_data)
    return u_data

async def start_game(game_key, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_key in GAMES_DATA:
        q, a = random.choice(GAMES_DATA[game_key])
        context.chat_data['game_ans'] = a
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🎮 بدأت لعبة {game_key}:\n\n【 {q} 】\n\n💰 الجائزة: 10 مليون دينار")
    elif game_key == "تخمين":
        num = str(random.randint(1, 10))
        context.chat_data['guess_num'] = num
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🎲 خمن الرقم من 1 لـ 10 (الجائزة 5 مليون)")
    elif game_key == "صيد":
        target = str(random.randint(1000, 9999))
        context.chat_data['hunt_num'] = target
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🎯 الأسرع يكتب الرقم: `{target}`")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, user_id, user_name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    parts = text.split()
    cmd = parts[0]
    curr_time = time.time()
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return
    u_data = await get_user_data(update)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- أوامر البنك الكاملة (بدون نقص) ---
    if cmd == "رصيدي": await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")
    elif cmd == "راتب":
        if curr_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق")
    elif cmd == "زرف":
        others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 1000000]
        if others:
            target = random.choice(others)
            amt = random.randint(1000000, 10000000)
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            db.update({'balance': max(0, target['balance'] - amt)}, User.id == target['id'])
            await update.message.reply_text(f"🥷 زرفت {amt:,} دينار من {target['name']}")
    elif cmd == "كنز":
        amt = random.randint(50000000, 100000000)
        db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        await update.message.reply_text(f"💎 لقيت كنز: {amt:,} دينار")
    elif cmd == "حظ":
        amt = random.randint(1000000, 50000000)
        res = amt if random.random() > 0.5 else -amt
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"🍀 نتيجة حظك: {res:,} دينار")
    elif cmd == "بخشيش":
        amt = random.randint(500000, 2000000); db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        await update.message.reply_text(f"☕ بخشيش: {amt:,} دينار")
    elif cmd == "استثمار":
        res = random.randint(-50000000, 100000000); db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"📈 استثمار: {res:,} دينار")
    elif cmd == "مضاربة":
        res = random.choice([20000000, -20000000]); db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"⚔️ مضاربة: {res:,} دينار")
    elif cmd == "هدية" and update.message.reply_to_message and len(parts) > 1:
        try:
            amt = int(parts[1])
            if u_data['balance'] >= amt > 0:
                t_id = update.message.reply_to_message.from_user.id
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                t_data = db.get(User.id == t_id)
                db.update({'balance': (t_data['balance'] if t_data else 0) + amt}, User.id == t_id)
                await update.message.reply_text(f"🎁 تم إرسال {amt:,} دينار هدية!")
        except: pass

    # --- الروليت وملك التفاعل ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")
    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data['r_starter'] or user_id == OWNER_ID:
            players = context.chat_data['r_players']
            if players:
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
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
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\nID : {win['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    # --- قائمة الألعاب بالأزرار ---
    elif text == "العاب":
        keyboard = [
            [InlineKeyboardButton("🟣 اسئله", callback_data="run_اسئله"), InlineKeyboardButton("🟣 دين", callback_data="run_دين"), InlineKeyboardButton("🟣 ثقافة", callback_data="run_ثقافه")],
            [InlineKeyboardButton("🟣 تخمين", callback_data="run_تخمين"), InlineKeyboardButton("🟣 صيد", callback_data="run_صيد"), InlineKeyboardButton("🟣 ترتيب", callback_data="run_ترتيب")],
            [InlineKeyboardButton("🟣 عكس", callback_data="run_عكس"), InlineKeyboardButton("🟣 تفكيك", callback_data="run_تفكيك"), InlineKeyboardButton("🟣 اعلام", callback_data="run_اعلام")],
            [InlineKeyboardButton("🟣 سيارات", callback_data="run_سيارات"), InlineKeyboardButton("🟣 عواصم", callback_data="run_عواصم"), InlineKeyboardButton("🟣 اندية", callback_data="run_اندية")],
            [InlineKeyboardButton("💰 البنك", callback_data="show_bank"), InlineKeyboardButton("🏆 التفاعل", callback_data="show_social")]
        ]
        await update.message.reply_text(f"🎮 **قائمة الألعاب** 🎮\n\nالمطور والمالك: {OWNER_NAME}\n\nاضغط على اسم اللعبة لبدء التحدي فوراً:", reply_markup=InlineKeyboardMarkup(keyboard))

    # التحقق من الإجابات
    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None; db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو {user_name}! صح وفزت بـ 10 مليون دينار!")
    if context.chat_data.get('guess_num') and text == context.chat_data['guess_num']:
        context.chat_data['guess_num'] = None; db.update({'balance': u_data['balance'] + 5000000}, User.id == user_id)
        await update.message.reply_text(f"🎯 صح! التخمين كان {text} وفزت بـ 5 مليون!")
    if context.chat_data.get('hunt_num') and text == context.chat_data['hunt_num']:
        context.chat_data['hunt_num'] = None; db.update({'balance': u_data['balance'] + 50000000}, User.id == user_id)
        await update.message.reply_text(f"🎯 قناص! صيد موفق وفزت بـ 50 مليون!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data.startswith("run_"):
        game_key = query.data.split("_")[1]
        await start_game(game_key, update, context)
    elif query.data == "show_bank":
        await query.message.reply_text("💰 **أوامر البنك:**\n(رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية)")
    elif query.data == "show_social":
        await query.message.reply_text("🏆 **أوامر التفاعل:**\n(روليت، ملك التفاعل، توب الروليت)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == '__main__': main()
