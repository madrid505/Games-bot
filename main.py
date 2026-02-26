# main.py
import logging, random, time, config, royal, games
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

db = TinyDB('bank_data.json')
User = Query()
logging.basicConfig(level=logging.INFO)

async def get_u(uid, name):
    u = db.get(User.id == uid)
    if not u:
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 الأسئلة", callback_data="tab_q"), InlineKeyboardButton("🎲 الحظ", callback_data="tab_l")],
        [InlineKeyboardButton("💰 البنك", callback_data="tab_b"), InlineKeyboardButton("🎰 روليت", callback_data="run_roulette")],
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="run_top")]
    ])

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_u(uid, name)

    # المستويات
    new_xp = u.get('xp', 0) + 1
    new_lvl = u.get('level', 1)
    if new_xp >= new_lvl * 50:
        new_lvl += 1
        await update.message.reply_text(f"🆙 كفو {name}! لفل {new_lvl}\nلقبك: {config.get_rank_name(new_lvl)}")
    db.update({'xp': new_xp, 'level': new_lvl, 'points': u.get('points', 0)+1, 'name': name}, User.id == uid)

    # تشغيل الألعاب بالنص
    clean = text.replace("لعبة ", "")
    if clean in games.ALL_QUESTIONS or clean in ["تخمين", "صيد"]:
        q, a = await games.get_game_data(clean) if clean in games.ALL_QUESTIONS else (None, None)
        if clean == "تخمين": q, a = "🎲 خمن رقم (1-10)", str(random.randint(1, 10))
        if clean == "صيد": a = str(random.randint(1000, 9999)); q = f"🎯 اكتب الرقم: `{a}`"
        if q: context.chat_data['ans'] = a; await update.message.reply_text(f"🎮 بدأت {clean}:\n【 {q} 】"); return

    # البنك والروليت
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 لفل: {u['level']}\n💰 رصيدك: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 راتب: {amt:,}")
        else: await update.message.reply_text("⏳ انتظر 10 دقائق!")
    elif text in ["كنز", "حظ", "بخشيش", "استثمار", "زرف"]:
        amt = random.randint(2000000, 40000000); res = amt if (random.random() > 0.45 or text == "كنز") else -amt
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid); await update.message.reply_text(f"💰 {text}: {res:,}")
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
        await update.message.reply_text(royal.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name}); await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_s'] or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res:
                await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
                if res['is_king']: await update.message.reply_text(royal.MSG_ROULETTE_KING.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False
    elif text == "ملك التفاعل": await update.message.reply_text(await royal.get_top_active())
    elif text == "العاب": await update.message.reply_text(f"🔱 قائمة {config.OWNER_NAME} 🔱", reply_markup=main_menu())

    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح {name}! +10 مليون")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "tab_q":
        btns = [[InlineKeyboardButton(k, callback_data=f"run_{k}") for k in list(games.ALL_QUESTIONS.keys())[i:i+2]] for i in range(0, len(games.ALL_QUESTIONS), 2)]
        await query.edit_message_text("🎮 اختر القسم:", reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        q, a = await games.get_game_data(key)
        if q: context.chat_data['ans'] = a; await query.message.reply_text(f"🎮 {key}:\n【 {q} 】")
    elif data == "run_top": await query.message.reply_text(await royal.get_top_active())

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(cb))
    app.run_polling()

if __name__ == '__main__': main()
