# main.py
import logging, random, time, config, royal, games
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

db = TinyDB('bank_data.json')
User = Query()

async def get_u(uid, name):
    u = db.get(User.id == uid); 
    if not u: 
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_u(uid, name)

    # --- المستويات ---
    new_xp = u.get('xp', 0) + 1
    if new_xp >= u['level'] * 50:
        db.update({'level': u['level']+1, 'xp': 0}, User.id == uid)
        await update.message.reply_text(f"🆙 كفو {name}! لفل {u['level']+1}")
    db.update({'xp': new_xp, 'points': u.get('points',0)+1}, User.id == uid)

    # --- أوامر البنك الكاملة ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 لفل: {u['level']}\n💰 رصيدك: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 راتب: {amt:,}")
        else: await update.message.reply_text("⏳ انتظر 10 دقائق!")
    elif text in ["زرف", "كنز", "حظ", "استثمار", "مضاربة", "بخشيش"]:
        res = random.randint(-10000000, 30000000)
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 {text}: {res:,} دينار")
    elif text.startswith("هدية "):
        try:
            gift = int(text.split()[1])
            if u['balance'] >= gift:
                db.update({'balance': u['balance']-gift}, User.id == uid)
                await update.message.reply_text(f"🎁 تم خصم {gift:,} من رصيدك لإرسال الهدية!")
            else: await update.message.reply_text("❌ رصيدك لا يكفي!")
        except: pass

    # --- الروليت (صلاحية المالك والمشرفين فقط) ---
    elif text == "روليت":
        stat = await context.bot.get_chat_member(update.effective_chat.id, uid)
        if uid == config.OWNER_ID or stat.status in ['creator', 'administrator']:
            context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
            await update.message.reply_text(royal.MSG_ROULETTE_START)
        else: await update.message.reply_text("⚠️ عذراً، الروليت للمدراء فقط!")

    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name}); await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_s'] or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res:
                await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
                if res['is_king']: await update.message.reply_text(royal.MSG_ROULETTE_KING.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False

    # --- الألعاب بالنص ---
    clean = text.replace("لعبة ", "")
    if clean in games.ALL_QUESTIONS or clean in ["تخمين", "صيد", "حرب العصابات", "السلم والحية", "المزاد"]:
        q, a = await games.get_game_data(clean) if clean in games.ALL_QUESTIONS else (f"بدأت {clean}!", "بدء")
        context.chat_data['ans'] = a; await update.message.reply_text(f"🎮 {clean}:\n{q}")

    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ كفو {name}! +10 مليون")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.run_polling()

if __name__ == '__main__': main()
