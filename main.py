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

def main_menu_kb():
    # قائمة مرتبة بأيقونات فخمة
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("☪️ أسئلة دينية", callback_data="run_دين"), InlineKeyboardButton("🌍 العواصم", callback_data="run_عواصم")],
        [InlineKeyboardButton("⚽ الأندية", callback_data="run_اندية"), InlineKeyboardButton("🎯 لعبة الصيد", callback_data="run_صيد")],
        [InlineKeyboardButton("⚔️ عصابات", callback_data="run_حرب العصابات"), InlineKeyboardButton("🍀 ساعة الحظ", callback_data="run_ساعة الحظ")],
        [InlineKeyboardButton("💣 القنبلة", callback_data="run_القنبلة"), InlineKeyboardButton("🔨 المزاد", callback_data="run_المزاد")],
        [InlineKeyboardButton("💰 البنك", callback_data="show_bank"), InlineKeyboardButton("🎰 روليت", callback_data="run_roulette")]
    ])

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    chat_id, uid, name = update.effective_chat.id, update.effective_user.id, update.effective_user.first_name
    
    # حماية الجروبات
    if chat_id not in config.ALLOWED_GROUPS and update.effective_chat.type != "private": return
    
    u = await get_u(uid, name)
    text = update.message.text.strip()

    # رد "بوت"
    if text == "بوت":
        await update.message.reply_text(config.MSG_BOT_REPLY); return
    
    # فتح القائمة
    if text == "العاب":
        await update.message.reply_text(f"🔱 **قائمة ألعاب الإمبراطور {config.OWNER_NAME}** 🔱", 
                                       reply_markup=main_menu_kb(), parse_mode="Markdown"); return

    # أوامر البنك (كاملة بلا نقص)
    bank_actions = ["حظ", "استثمار", "مضاربة", "بخشيش", "زرف", "كنز"]
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 لفل: {u['level']}\n💰 الرصيد: {u['balance']:,}"); return
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 راتب: {amt:,}"); return
        else: await update.message.reply_text("⏳ انتظِر 10 دقائق!"); return
    elif text in bank_actions:
        res = random.randint(-20000000, 50000000)
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 {text}: {'ربحت' if res > 0 else 'خسرت'} {abs(res):,} دينار"); return
    elif text.startswith("هدية "):
        try:
            val = int(text.split()[1])
            if u['balance'] >= val:
                db.update({'balance': u['balance']-val}, User.id == uid)
                await update.message.reply_text(f"🎁 تم إرسال هدية بقيمة {val:,}"); return
            else: await update.message.reply_text("❌ رصيدك ناقص!"); return
        except: pass

    # الروليت (نظام المشرفين)
    if text == "روليت":
        stat = await context.bot.get_chat_member(chat_id, uid)
        if uid == config.OWNER_ID or stat.status in ['creator', 'administrator']:
            context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
            await update.message.reply_text(royal.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name})
        await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_s'] or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res: await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False

    # تشغيل الألعاب النصية
    clean = text.replace("لعبة ", "")
    q, a = await games.get_game_data(clean)
    if q:
        if q in ["WIN", "LOSE"]:
            change = a if q == "WIN" else -a
            db.update({'balance': max(0, u['balance']+change)}, User.id == uid)
            await update.message.reply_text(f"{'✅' if q=='WIN' else '💀'} {clean}: {('ربحت' if q=='WIN' else 'خسرت')} {a:,}")
        else:
            context.chat_data['ans'] = a; await update.message.reply_text(f"🎮 {clean}:\n{q}")

    # التحقق من الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح يا {name}! +10,000,000")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data.startswith("run_"):
        key = data.split("_")[1]; q, a = await games.get_game_data(key)
        if q in ["WIN", "LOSE"]:
            await query.message.reply_text(f"اكتب 'لعبة {key}' لتبدأ المراهنة!"); return
        if q: context.chat_data['ans'] = a; await query.message.reply_text(f"🎮 {key}:\n{q}")
    elif data == "show_bank":
        await query.message.reply_text("💰 أوامر البنك: (رصيدي، راتب، هدية، حظ، استثمار، مضاربة، بخشيش، زرف، كنز)")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(cb))
    app.run_polling()

if __name__ == '__main__': main()
