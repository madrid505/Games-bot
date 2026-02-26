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
    # قائمة فخمة ومرتبة
    btns = [
        [InlineKeyboardButton("☪️ دين", callback_data="run_دين"), InlineKeyboardButton("🌍 عواصم", callback_data="run_عواصم")],
        [InlineKeyboardButton("⚽ أندية", callback_data="run_اندية"), InlineKeyboardButton("💣 القنبلة", callback_data="run_القنبلة")],
        [InlineKeyboardButton("⚔️ عصابات", callback_data="run_حرب العصابات"), InlineKeyboardButton("🍀 ساعة الحظ", callback_data="run_ساعة الحظ")],
        [InlineKeyboardButton("🔨 المزاد", callback_data="run_المزاد"), InlineKeyboardButton("🎯 صيد", callback_data="run_صيد")],
        [InlineKeyboardButton("💰 البنك", callback_data="tab_bank"), InlineKeyboardButton("🎰 روليت", callback_data="run_roulette")]
    ]
    return InlineKeyboardMarkup(btns)

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    chat_id, uid, name = update.effective_chat.id, update.effective_user.id, update.effective_user.first_name
    if chat_id not in config.ALLOWED_GROUPS and update.effective_chat.type != "private": return
    
    u = await get_u(uid, name)
    text = update.message.text.strip()

    # 1. ردود الأفعال الأساسية
    if text == "بوت":
        await update.message.reply_text(config.MSG_BOT_REPLY); return
    elif text == "العاب":
        await update.message.reply_text("🔱 **قائمة ألعاب الإمبراطور** 🔱", reply_markup=main_menu_kb(), parse_mode="Markdown"); return

    # 2. أوامر البنك الكاملة (تم تحديثها)
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 المستوى: {u['level']}\n💰 الرصيد: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000); db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 تم استلام راتبك الملكي: {amt:,}")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق يا ملك!")
    elif text in ["حظ", "استثمار", "مضاربة", "بخشيش", "زرف", "كنز"]:
        res = random.randint(-20000000, 50000000); db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 {text}: {'ربحت' if res > 0 else 'خسرت'} {abs(res):,} دينار")
    elif text.startswith("هدية "):
        try:
            val = int(text.split()[1]); 
            if u['balance'] >= val:
                db.update({'balance': u['balance']-val}, User.id == uid)
                await update.message.reply_text(f"🎁 كفو! أرسلت هدية بقيمة {val:,}")
            else: await update.message.reply_text("❌ رصيدك لا يسمح!")
        except: pass

    # 3. الروليت (صلاحية المدراء)
    elif text == "روليت":
        stat = await context.bot.get_chat_member(chat_id, uid)
        if uid == config.OWNER_ID or stat.status in ['creator', 'administrator']:
            context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
            await update.message.reply_text(royal.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name}); await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data.get('r_s') or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res:
                await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False

    # 4. تشغيل الألعاب (نص + زر)
    clean = text.replace("لعبة ", "")
    q, a = await games.get_game_data(clean)
    if q:
        if q == "WIN":
            db.update({'balance': u['balance']+a}, User.id == uid)
            await update.message.reply_text(f"✅ كفو! فزت في {clean} بـ {a:,}")
        elif q == "LOSE":
            db.update({'balance': max(0, u['balance']-a)}, User.id == uid)
            await update.message.reply_text(f"💀 للأسف! خسرت في {clean} مبلغ {a:,}")
        else:
            context.chat_data['ans'] = a; await update.message.reply_text(f"🎮 {clean}:\n{q}")

    # 5. تحقق الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح! +10,000,000")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data.startswith("run_"):
        key = data.split("_")[1]; q, a = await games.get_game_data(key)
        if q == "WIN": await query.message.reply_text(f"✅ فزت بـ {a:,}"); return
        if q: context.chat_data['ans'] = a; await query.message.reply_text(f"🎮 {key}:\n{q}")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(cb))
    app.run_polling()

if __name__ == '__main__': main()
