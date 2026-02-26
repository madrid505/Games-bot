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

# --- بيانات الألعاب والشرح ---
GAMES_INFO = {
    "اسئله": {"cmd": "اسئله", "desc": "جاوب على أسئلة عامة متنوعة."},
    "دين": {"cmd": "دين", "desc": "أسئلة إسلامية وثقافية دينية."},
    "تخمين": {"cmd": "تخمين", "desc": "خمن الرقم من 1 لـ 10 واربح."},
    "قنبلة": {"cmd": "قنبلة", "desc": "مرر القنبلة قبل أن تنفجر فيك!"},
    "مزاد": {"cmd": "مزاد + المبلغ", "desc": "زايد بأموالك على جوائز المالك."},
    "صيد": {"cmd": "صيد", "desc": "كن الأسرع في كتابة الرقم المكتوب."},
    "حرب": {"cmd": "حرب", "desc": "تحدي تجميع نقاط التفاعل بين فريقين."},
    "ساعة الحظ": {"cmd": "ساعة الحظ", "desc": "وقت الرواتب المضاعفة (للمالك فقط)."},
    "ترتيب": {"cmd": "ترتيب", "desc": "رتب الحروف المبعثرة لتكوين كلمة."},
    "عكس": {"cmd": "عكس", "desc": "اكتب الكلمة بشكل معكوس بسرعة."},
    "تفكيك": {"cmd": "تفكيك", "desc": "فكك الكلمة إلى حروف متباعدة."},
    "اعلام": {"cmd": "اعلام", "desc": "اكتب اسم الدولة التي ينتمي لها العلم."},
    "سيارات": {"cmd": "سيارات", "desc": "تحدي في أسماء ماركات السيارات."},
    "عواصم": {"cmd": "عواصم", "desc": "اكتب عاصمة الدولة المطلوبة."},
    "كلمات": {"cmd": "كلمات", "desc": "اكتب الكلمة المعروضة بأسرع وقت."},
    "المختلف": {"cmd": "المختلف", "desc": "استخرج الكلمة المختلفة عن البقية."},
    "اندية": {"cmd": "اندية", "desc": "تحدي في أسماء الأندية واللاعبين."}
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
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- أوامر البنك الكاملة ---
    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")
    elif cmd == "راتب":
        if curr_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr_time}, User.id == user_id)
            await update.message.reply_text(f"💵 تم إيداع راتبك: {amt:,} دينار")
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
        await update.message.reply_text(f"🍀 حظك: {res:,} دينار")
    elif cmd == "بخشيش":
        amt = random.randint(500000, 2000000)
        db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
        await update.message.reply_text(f"☕ بخشيش: {amt:,} دينار")
    elif cmd == "استثمار":
        res = random.randint(-50000000, 100000000)
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"📈 استثمار: {res:,} دينار")
    elif cmd == "مضاربة":
        res = random.choice([20000000, -20000000])
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"⚔️ مضاربة: {res:,} دينار")
    elif cmd == "هدية" and update.message.reply_to_message and len(parts) > 1:
        try:
            amt = int(parts[1])
            t_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= amt > 0:
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                t_data = db.get(User.id == t_id)
                db.update({'balance': (t_data['balance'] if t_data else 0) + amt}, User.id == t_id)
                await update.message.reply_text(f"🎁 أرسلت {amt:,} دينار هدية!")
        except: pass

    # --- الروليت (تكرار انا مسموح) ---
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

    # --- ملك التفاعل ---
    elif text == "ملك التفاعل":
        all_u = db.all()
        if all_u:
            win = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\nID : {win['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    # --- القائمة الرئيسية بالأزرار ---
    elif text == "العاب":
        keyboard = [
            [InlineKeyboardButton("🟣 اسئله", callback_data="g_اسئله"), InlineKeyboardButton("🟣 دين", callback_data="g_دين")],
            [InlineKeyboardButton("🟣 تخمين", callback_data="g_تخمين"), InlineKeyboardButton("🟣 قنبلة", callback_data="g_قنبلة")],
            [InlineKeyboardButton("🟣 مزاد", callback_data="g_مزاد"), InlineKeyboardButton("🟣 صيد", callback_data="g_صيد")],
            [InlineKeyboardButton("🟣 حرب", callback_data="g_حرب"), InlineKeyboardButton("🟣 ترتيب", callback_data="g_ترتيب")],
            [InlineKeyboardButton("🟣 عكس", callback_data="g_عكس"), InlineKeyboardButton("🟣 تفكيك", callback_data="g_تفكيك")],
            [InlineKeyboardButton("🟣 اعلام", callback_data="g_اعلام"), InlineKeyboardButton("🟣 سيارات", callback_data="g_سيارات")],
            [InlineKeyboardButton("💰 البنك", callback_data="g_bank"), InlineKeyboardButton("🏆 التفاعل", callback_data="g_social")]
        ]
        await update.message.reply_text(f"🍷🍷 **قائمة أساطير {OWNER_NAME}** 🍷🍷\n\nاختر المسابقة التي تريد شرحها وبدءها:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("g_"):
        key = data.split("_")[1]
        if key == "bank":
            msg = "💰 **أوامر البنك:**\n(رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية)"
        elif key == "social":
            msg = "🏆 **التفاعل:**\n(روليت، ملك التفاعل، توب الروليت)"
        elif key in GAMES_INFO:
            info = GAMES_INFO[key]
            msg = f"💜 **لعبة {key}** 💜\n\n📝 الشرح: {info['desc']}\n\n⌨️ الأمر للبدء: `{info['cmd']}`"
        else: msg = "قسم قادم..."
        await query.edit_message_text(msg, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == '__main__': main()
