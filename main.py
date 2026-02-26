# main.py
import time, config, royal, games, random
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

def get_menu(page=1):
    if page == 1:
        btns = [
            [InlineKeyboardButton("☪️ دين", callback_data="run_دين"), InlineKeyboardButton("🌍 عواصم", callback_data="run_عواصم")],
            [InlineKeyboardButton("⚽ أندية", callback_data="run_اندية"), InlineKeyboardButton("🚩 أعلام", callback_data="run_أعلام")],
            [InlineKeyboardButton("➡️ الصفحة التالية", callback_data="page_2")]
        ]
    else:
        btns = [
            [InlineKeyboardButton("⚔️ عصابات", callback_data="run_حرب العصابات"), InlineKeyboardButton("💣 القنبلة", callback_data="run_القنبلة")],
            [InlineKeyboardButton("🔨 المزاد", callback_data="run_المزاد"), InlineKeyboardButton("🎯 صيد", callback_data="run_صيد")],
            [InlineKeyboardButton("🔙 العودة", callback_data="page_1")]
        ]
    return InlineKeyboardMarkup(btns)

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    chat_id, uid, name = update.effective_chat.id, update.effective_user.id, update.effective_user.first_name
    if chat_id not in config.ALLOWED_GROUPS and update.effective_chat.type != "private": return
    
    u = await get_u(uid, name)
    text = update.message.text.strip()

    # أوامر عامة
    if text == "بوت": await update.message.reply_text(config.MSG_BOT_REPLY); return
    if text == "العاب": await update.message.reply_text("🔱 قائمة ألعاب الإمبراطور 🔱", reply_markup=get_menu(1)); return
    if text == "تفاعل": res = await royal.get_top_active(); await update.message.reply_text(res); return

    # نظام ساعة الحظ (تفعيل للأدمن)
    if text == "تفعيل ساعة الحظ" and uid == config.OWNER_ID:
        context.chat_data['lucky_hour'] = True
        await update.message.reply_text("🍀 تم تفعيل ساعة الحظ! مبالغ الزرف والراتب والجوائز مضاعفة الآن!"); return

    # أوامر البنك
    bank_cmds = ["حظ", "استثمار", "مضاربة", "بخشيش", "زرف", "كنز"]
    if text == "رصيدي": await update.message.reply_text(f"👤 {name}\n💰 الرصيد: {u['balance']:,}"); return
    if text == "راتب":
        is_lucky = context.chat_data.get('lucky_hour', False)
        if time.time() - u.get('last_salary', 0) > (300 if is_lucky else 600):
            amt = random.randint(20000000, 50000000) if is_lucky else random.randint(5000000, 20000000)
            db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 تم استلام راتبك {'المضاعف 🍀' if is_lucky else ''}: {amt:,}"); return
        else: await update.message.reply_text("⏳ انتظِر الوقت المحدد!"); return
    if text in bank_cmds:
        is_lucky = context.chat_data.get('lucky_hour', False)
        res = random.randint(10000000, 60000000) if is_lucky else random.randint(-15000000, 40000000)
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 {text}: {'ربحت' if res > 0 else 'خسرت'} {abs(res):,} دينار"); return
    if text.startswith("هدية "):
        try:
            parts = text.split()
            val = int(parts[1])
            if u['balance'] >= val:
                db.update({'balance': u['balance']-val}, User.id == uid)
                await update.message.reply_text(f"🎁 كفو يا {name}! تم إرسال هدية بقيمة {val:,}"); return
        except: pass

    # الروليت الملكي
    if text == "روليت":
        stat = await context.bot.get_chat_member(chat_id, uid)
        if uid == config.OWNER_ID or stat.status in ['creator', 'administrator']:
            context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
            await update.message.reply_text(royal.MSG_ROULETTE_START)
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name}); await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_s'] or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res: await update.message.reply_text(royal.MSG_ROULETTE_KING.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False

    # تشغيل الألعاب (نص أو أزرار)
    clean = text.replace("لعبة ", "")
    q, a = await games.get_game_data(clean, context.chat_data.get('lucky_hour', False))
    if q:
        if q in ["WIN", "LOSE"]:
            change = a if q == "WIN" else -a
            db.update({'balance': max(0, u['balance']+change)}, User.id == uid)
            await update.message.reply_text(f"{'✅' if q=='WIN' else '💀'} {clean}: {('ربحت' if q=='WIN' else 'خسرت')} {a:,}")
        else:
            context.chat_data['ans'] = a; await update.message.reply_text(f"🎮 {clean}:\n{q}")

    # التحقق من الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None; db.update({'balance': u['balance'] + 10000000, 'points': u.get('points',0)+1}, User.id == uid)
        await update.message.reply_text(f"✅ إجابة صحيحة يا {name}! +10,000,000")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data.startswith("page_"):
        p = int(data.split("_")[1]); await query.edit_message_reply_markup(reply_markup=get_menu(p))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        if key == "roulette": await query.message.reply_text("اكتب 'روليت' لبدء الجولة!"); return
        q, a = await games.get_game_data(key, context.chat_data.get('lucky_hour', False))
        if q in ["WIN", "LOSE"]: await query.message.reply_text(f"اكتب 'لعبة {key}' للمراهنة!"); return
        if q: context.chat_data['ans'] = a; await query.message.reply_text(f"🎮 {key}:\n{q}")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(cb))
    app.run_polling()

if __name__ == '__main__': main()
