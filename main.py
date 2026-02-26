import logging, random, time
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters
import config # استيراد الملف الأول

db = TinyDB('bank_data.json')
User = Query()

async def get_u(uid, name):
    u = db.get(User.id == uid)
    if not u:
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

# دالة تشغيل الألعاب (زر + نص)
async def start_game(game_key, update, context):
    if game_key in config.GAMES_DATA:
        q, a = random.choice(config.GAMES_DATA[game_key])
        context.chat_data['ans'] = a
        await update.effective_message.reply_text(f"🎮 بدأت لعبة {game_key}:\n\n【 {q} 】")
    elif game_key == "تخمين":
        context.chat_data['ans'] = str(random.randint(1, 10))
        await update.effective_message.reply_text("🎲 خمن الرقم من 1 لـ 10")
    elif game_key == "صيد":
        t = str(random.randint(1000, 9999)); context.chat_data['ans'] = t
        await update.effective_message.reply_text(f"🎯 الأسرع يكتب الرقم: `{t}`")

# نظام التبويبات (Tabs)
def main_menu():
    kb = [
        [InlineKeyboardButton("🎮 ألعاب الأسئلة", callback_data="tab_q"), InlineKeyboardButton("🎲 ألعاب الحظ", callback_data="tab_l")],
        [InlineKeyboardButton("💰 البنك", callback_data="tab_b"), InlineKeyboardButton("🎰 روليت", callback_data="run_roulette")],
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="run_top")]
    ]
    return InlineKeyboardMarkup(kb)

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_u(uid, name)

    # نظام المستويات والخبرة (تعمل مع كل رسالة)
    new_xp = u.get('xp', 0) + 1
    new_lvl = u.get('level', 1)
    if new_xp >= new_lvl * 50:
        new_lvl += 1
        await update.message.reply_text(f"🆙 كفو {name}! وصلت لفل {new_lvl}\nلقبك: {config.get_rank(new_lvl)}")
    db.update({'xp': new_xp, 'level': new_lvl, 'points': u.get('points', 0)+1, 'name': name}, User.id == uid)

    # --- استجابة النص (تشغيل الألعاب بالاسم) ---
    clean = text.replace("لعبة ", "")
    if clean in config.GAMES_DATA or clean in ["تخمين", "صيد"]:
        await start_game(clean, update, context)
        return

    # --- أوامر البنك النصية ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n🎖 اللقب: {config.get_rank(u['level'])}\n📈 المستوى: {u['level']}\n💰 الرصيد: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,}")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")
    elif text in ["كنز", "حظ", "بخشيش", "استثمار", "زرف"]:
        amt = random.randint(2000000, 40000000); res = amt if (random.random() > 0.45 or text == "كنز") else -amt
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid); await update.message.reply_text(f"💰 {text}: {res:,}")

    # --- الروليت الملكي (المحافظة عليه كما طلبت) ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], uid
        await update.message.reply_text(config.MSG_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': uid, 'name': name})
        await update.message.reply_text(config.MSG_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_starter'] or uid == config.OWNER_ID:
            ps = context.chat_data.get('r_players', [])
            if ps:
                win = random.choice(ps); w_db = await get_u(win['id'], win['name'])
                nw = w_db.get('roulette_wins', 0) + 1; db.update({'roulette_wins': nw}, User.id == win['id'])
                await update.message.reply_text(config.MSG_WIN.format(name=win['name'], wins=nw))
                if nw >= 5:
                    await update.message.reply_text(config.MSG_KING.format(name=win['name'], wins=nw))
                    for usr in db.all(): db.update({'roulette_wins': 0}, User.id == usr['id'])
            context.chat_data['r_on'] = False

    elif text == "ملك التفاعل":
        top = max(db.all(), key=lambda x: x.get('points', 0))
        await update.message.reply_text(f"🔥🔥 ملك التفاعل: {top['name']}\nالنقاط: {top['points']}")
    
    elif text == "العاب":
        await update.message.reply_text("قائمة الألعاب الإمبراطورية:", reply_markup=main_menu())

    # تحقق الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح يا {name}! +10 مليون")

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "tab_q":
        btns = [[InlineKeyboardButton(k, callback_data=f"run_{k}") for k in list(config.GAMES_DATA.keys())[i:i+2]] for i in range(0, len(config.GAMES_DATA), 2)]
        await query.edit_message_text("🎮 ألعاب الأسئلة:", reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("run_"):
        await start_game(data.split("_")[1], update, context)
    elif data == "run_top":
        top = max(db.all(), key=lambda x: x.get('points', 0))
        await query.message.reply_text(f"👑 ملك التفاعل: {top['name']} ({top['points']} نقطة)")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.run_polling()

if __name__ == '__main__': main()
