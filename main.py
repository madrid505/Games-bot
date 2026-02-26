# main.py
import logging, random, time, config, royal, games
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

db = TinyDB('bank_data.json')
User = Query()

async def get_u(uid, name):
    u = db.get(User.id == uid)
    if not u:
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

def games_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 أسئلة", callback_data="tab_q"), InlineKeyboardButton("🎲 مسابقات", callback_data="tab_m")],
        [InlineKeyboardButton("💰 بنك", callback_data="tab_b"), InlineKeyboardButton("🎰 روليت", callback_data="run_roulette")],
        [InlineKeyboardButton("👑 التفاعل", callback_data="run_top")]
    ])

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    chat_id = update.effective_chat.id
    if chat_id not in config.ALLOWED_GROUPS and update.effective_chat.type != "private": return

    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_u(uid, name)

    # رد "بوت" و "العاب"
    if text == "بوت":
        await update.message.reply_text(config.MSG_BOT_REPLY); return
    elif text == "العاب":
        await update.message.reply_text(f"🔱 ألعاب {config.OWNER_NAME} 🔱", reply_markup=games_menu()); return

    # أوامر البنك (حظ، استثمار، مضاربة، بخشيش، هدية)
    bank_cmds = ["حظ", "استثمار", "مضاربة", "بخشيش", "زرف", "كنز"]
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 لفل: {u['level']}\n💰 رصيدك: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 راتب: {amt:,}")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")
    elif text in bank_cmds:
        res = random.randint(-15000000, 40000000); db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 {text}: {res:,} دينار")
    elif text.startswith("هدية "):
        try:
            val = int(text.split()[1])
            if u['balance'] >= val:
                db.update({'balance': u['balance']-val}, User.id == uid)
                await update.message.reply_text(f"🎁 تم خصم {val:,} لهديتك!")
            else: await update.message.reply_text("❌ رصيدك لا يكفي!")
        except: pass

    # الروليت وملك التفاعل
    elif text == "روليت":
        stat = await context.bot.get_chat_member(chat_id, uid)
        if uid == config.OWNER_ID or stat.status in ['creator', 'administrator']:
            context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
            await update.message.reply_text(royal.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name})
        await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data.get('r_s') or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res:
                await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
                if res['is_king']: await update.message.reply_text(royal.MSG_ROULETTE_KING.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False
    elif text == "ملك التفاعل":
        await update.message.reply_text(await royal.get_top_active())

    # تشغيل الألعاب (نص)
    clean = text.replace("لعبة ", "")
    q, a = await games.get_game_data(clean)
    if q:
        if q == "WIN":
            db.update({'balance': u['balance']+a}, User.id == uid)
            await update.message.reply_text(f"✅ فزت في {clean} بربح {a:,}!")
        elif q == "LOSE":
            db.update({'balance': max(0, u['balance']-a)}, User.id == uid)
            await update.message.reply_text(f"❌ خسرت في {clean} مبلغ {a:,}!")
        else:
            context.chat_data['ans'] = a; await update.message.reply_text(f"🎮 {clean}:\n{q}")

    # تحقق الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ كفو {name}! +10 مليون")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "tab_q":
        btns = [[InlineKeyboardButton(k, callback_data=f"run_{k}") for k in ["دين", "عواصم", "اندية"]]]
        await query.edit_message_text("🎮 اختر قسم الأسئلة:", reply_markup=InlineKeyboardMarkup(btns))
    elif data == "tab_m":
        btns = [[InlineKeyboardButton(k, callback_data=f"run_{k}") for k in ["تخمين", "صيد", "حرب العصابات", "السلم والحية", "المزاد"]]]
        await query.edit_message_text("🎲 اختر مسابقة:", reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("run_"):
        key = data.split("_")[1]; q, a = await games.get_game_data(key)
        if q: context.chat_data['ans'] = a; await query.message.reply_text(f"🎮 {key}:\n{q}")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(cb))
    app.run_polling()

if __name__ == '__main__': main()
