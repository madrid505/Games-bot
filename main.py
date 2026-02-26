import logging, random, time
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.setchatdescription import SetChatDescription
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

# استيراد الملفات المنفصلة
import royal
import games

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🇳🇦🇸 ♛༒۝༻"

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- دالة جلب بيانات المستخدم ---
async def get_u(uid, name):
    u = db.get(User.id == uid)
    if not u:
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

# --- نظام التبويبات (Tabs) ---
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 ألعاب الأسئلة", callback_data="tab_q"), InlineKeyboardButton("🎲 ألعاب الحظ", callback_data="tab_l")],
        [InlineKeyboardButton("💰 خدمات البنك", callback_data="tab_b"), InlineKeyboardButton("🎰 روليت ملكي", callback_data="run_roulette")],
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="run_top")]
    ])

# --- المعالج الرئيسي (النص + المستويات + البنك) ---
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_u(uid, name)

    # 1. تحديث المستوى (شغال مع كل رسالة)
    new_xp = u.get('xp', 0) + 1
    new_lvl = u.get('level', 1)
    if new_xp >= new_lvl * 50:
        new_lvl += 1
        await update.message.reply_text(f"🆙 كفو {name}! وصلت لفل {new_lvl}\nلقبك: {royal.get_rank(new_lvl) if hasattr(royal, 'get_rank') else 'عضو متميز'}")
    db.update({'xp': new_xp, 'level': new_lvl, 'points': u.get('points', 0)+1, 'name': name}, User.id == uid)

    # 2. تشغيل الألعاب بالنص (دمج كامل)
    clean = text.replace("لعبة ", "")
    if clean in games.ALL_QUESTIONS or clean in ["تخمين", "صيد"]:
        q, a = await games.get_game_data(clean) if clean in games.ALL_QUESTIONS else (None, None)
        if clean == "تخمين": q, a = "🎲 خمن رقم من 1-10", str(random.randint(1, 10))
        if clean == "صيد": a = str(random.randint(1000, 9999)); q = f"🎯 اكتب الرقم بسرعة: `{a}`"
        
        if q:
            context.chat_data['ans'] = a
            await update.message.reply_text(f"🎮 بدأت {clean}:\n\n【 {q} 】")
            return

    # 3. أوامر البنك والرسائل الملكية
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 المستوى: {u['level']}\n💰 الرصيد: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 راتبك الملكي: {amt:,}")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")
    elif text in ["كنز", "حظ", "بخشيش", "استثمار", "زرف"]:
        amt = random.randint(2000000, 40000000); res = amt if (random.random() > 0.45 or text == "كنز") else -amt
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid); await update.message.reply_text(f"💰 {text}: {res:,}")

    # 4. الروليت (من الملف الملكي royal.py)
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
        await update.message.reply_text(royal.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name})
        await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_s'] or uid == OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res:
                await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
                if res['is_king']: await update.message.reply_text(royal.MSG_ROULETTE_KING.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False

    elif text == "ملك التفاعل":
        msg = await royal.get_top_active()
        await update.message.reply_text(msg)
    
    elif text == "العاب":
        await update.message.reply_text(f"🔱 قائمة ألعاب {OWNER_NAME} 🔱", reply_markup=main_menu_kb())

    # 5. تحقق الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح يا {name}! فزت بـ 10,000,000")

# --- معالج الأزرار ---
async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "tab_q":
        btns = [[InlineKeyboardButton(k, callback_data=f"run_{k}") for k in list(games.ALL_QUESTIONS.keys())[i:i+2]] for i in range(0, len(games.ALL_QUESTIONS), 2)]
        await query.edit_message_text("🎮 اختر قسم الأسئلة:", reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        q, a = await games.get_game_data(key)
        if q: context.chat_data['ans'] = a; await query.message.reply_text(f"🎮 {key}:\n\n【 {q} 】")
    elif data == "run_top":
        await query.message.reply_text(await royal.get_top_active())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(cb))
    print("🚀 البوت الإمبراطوري جاهز للعمل...")
    app.run_polling()

if __name__ == '__main__': main()
