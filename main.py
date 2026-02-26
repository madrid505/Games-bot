import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

# استيراد الإعدادات والرسائل من الملف الأول
try:
    import config
except ImportError:
    print("خطأ: يرجى التأكد من وجود ملف config.py في نفس المجلد!")

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- دالة الحصول على بيانات المستخدم ---
async def get_user_data(uid, name):
    u = db.get(User.id == uid)
    if not u:
        balance = 1000000000000 if uid == config.OWNER_ID else 10000000000
        u = {'id': uid, 'name': name, 'balance': balance, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

# --- نظام التبويبات (Tabs System) ---
def get_tabs_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎮 ألعاب الأسئلة", callback_data="tab_questions"),
         InlineKeyboardButton("🎲 ألعاب الحظ", callback_data="tab_luck")],
        [InlineKeyboardButton("💰 خدمات البنك", callback_data="tab_bank"),
         InlineKeyboardButton("🎰 الروليت الملكي", callback_data="run_roulette")],
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="run_top_active")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- قائمة الأسئلة (تبويب 1) ---
def get_questions_menu():
    keys = [("🌙 دين", "run_دين"), ("🗺 عواصم", "run_عواصم"), ("⚽ أندية", "run_اندية"), 
            ("🧠 ترتيب", "run_ترتيب"), ("🇺🇸 إنجليزي", "run_انجليزي"), ("🔢 رياضيات", "run_رياضيات")]
    btns = [[InlineKeyboardButton(k[0], callback_data=k[1]) for k in keys[i:i+2]] for i in range(0, len(keys), 2)]
    btns.append([InlineKeyboardButton("🔙 العودة للقائمة", callback_data="main_menu")])
    return InlineKeyboardMarkup(btns)

# --- قائمة الحظ والألعاب الـ 5 (تبويب 2) ---
def get_luck_menu():
    keys = [("🎯 صيد", "run_صيد"), ("🎲 تخمين", "run_تخمين"), ("⚔️ حرب", "shrah_gang"), 
            ("🐍 سلم", "shrah_ladder"), ("🔨 مزاد", "shrah_auction"), ("🍀 حظ", "shrah_lucky")]
    btns = [[InlineKeyboardButton(k[0], callback_data=k[1]) for k in keys[i:i+2]] for i in range(0, len(keys), 2)]
    btns.append([InlineKeyboardButton("🔙 العودة للقائمة", callback_data="main_menu")])
    return InlineKeyboardMarkup(btns)

# --- المعالج الرئيسي للرسائل (نظام المستويات + أوامر البنك النصية) ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_user_data(uid, name)

    # تحديث المستويات (تعمل مع كل رسالة)
    new_xp = u.get('xp', 0) + 1
    new_lvl = u.get('level', 1)
    if new_xp >= new_lvl * 50:
        new_lvl += 1
        await update.message.reply_text(f"🆙 كفو {name}! ارتفع مستواك لـ {new_lvl}\nلقبك الجديد: {config.get_user_rank(new_lvl)}")
    db.update({'xp': new_xp, 'level': new_lvl, 'points': u.get('points', 0)+1, 'name': name}, User.id == uid)

    # --- أوامر البنك (تعمل نصياً) ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 الاسم: {name}\n🎖 اللقب: {config.get_user_rank(u['level'])}\n📈 المستوى: {u['level']}\n💰 الرصيد: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 نزل راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")
    elif text in ["كنز", "حظ", "بخشيش", "استثمار", "زرف"]:
        amt = random.randint(2000000, 40000000); res = amt if (random.random() > 0.45 or text == "كنز") else -amt
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 نتيجة {text}: {res:,} دينار")

    # --- نظام الروليت الملكي (نصي) ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], uid
        await update.message.reply_text(config.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': uid, 'name': name})
        await update.message.reply_text(config.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data.get('r_starter') or uid == config.OWNER_ID:
            players = context.chat_data.get('r_players', [])
            if players:
                win = random.choice(players); w_db = await get_user_data(win['id'], win['name'])
                new_w = w_db.get('roulette_wins', 0) + 1; db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(config.MSG_ROULETTE_WIN.format(name=win['name'], wins=new_w))
                if new_w >= 5:
                    await update.message.reply_text(config.MSG_ROULETTE_KING.format(name=win['name'], wins=new_w))
                    for usr in db.all(): db.update({'roulette_wins': 0}, User.id == usr['id'])
            context.chat_data['r_on'] = False

    elif text == "ملك التفاعل":
        top = max(db.all(), key=lambda x: x.get('points', 0))
        await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {top['name']}\n\nعدد النقاط : {top['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")

    elif text == "العاب":
        await update.message.reply_text(f"قائمة الألعاب - المالك: {config.OWNER_NAME}", reply_markup=get_tabs_keyboard())

    # تحقق الإجابة للألعاب
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح يا {name}! فزت بـ 10 مليون!")

# --- معالج الأزرار (نظام التبويبات والمسارات الفريدة) ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data, uid = query.data, query.from_user.id
    
    if data == "main_menu":
        await query.edit_message_text(f"قائمة الألعاب - المالك: {config.OWNER_NAME}", reply_markup=get_tabs_keyboard())
    elif data == "tab_questions":
        await query.edit_message_text("🎮 اختر نوع الأسئلة:", reply_markup=get_questions_menu())
    elif data == "tab_luck":
        await query.edit_message_text("🎲 ألعاب الحظ والمخاطرة:", reply_markup=get_luck_menu())
    elif data == "tab_bank":
        await query.message.reply_text("💰 أوامر البنك: (رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، هدية)")
    
    elif data.startswith("run_"):
        key = data.split("_")[1]
        if key in config.GAMES_DATABASE:
            q, a = random.choice(config.GAMES_DATABASE[key]); context.chat_data['ans'] = a
            await query.message.reply_text(f"🎮 بدأت {key}:\n\n【 {q} 】")
        elif key == "تخمين":
            context.chat_data['ans'] = str(random.randint(1, 10))
            await query.message.reply_text("🎲 خمن الرقم من 1 لـ 10")
        elif key == "صيد":
            target = str(random.randint(1000, 9999)); context.chat_data['ans'] = target
            await query.message.reply_text(f"🎯 الأسرع يكتب الرقم: `{target}`")
        elif key == "top_active":
             top = max(db.all(), key=lambda x: x.get('points', 0))
             await query.message.reply_text(f"🔥🔥 ملك التفاعل: {top['name']}\nالنقاط: {top['points']}")

    elif data.startswith("shrah_"):
        key = data.split("_")[1]
        btns = [[InlineKeyboardButton("🚀 ابدأ الآن", callback_data=f"run_{key}")], [InlineKeyboardButton("🔙 عودة", callback_data="tab_luck")]]
        await query.message.reply_text(f"📖 شرح {key}: العب واربح ملايين الدنانير واستمتع بالتحدي!", reply_markup=InlineKeyboardMarkup(btns))

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("إمبراطور مونوبولي يعمل الآن...")
    app.run_polling()

if __name__ == '__main__': main()
