# main.py
import logging, random, time, config, royal, games
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

db = TinyDB('bank_data.json')
User = Query()

async def get_u(uid, name):
    u = db.get(User.id == uid)
    if not u:
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    # حماية المجموعات المسموحة فقط
    if chat_id not in config.ALLOWED_GROUPS and update.effective_chat.type != "private":
        return

    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_u(uid, name)

    # رد "بوت"
    if text == "بوت":
        await update.message.reply_text(config.MSG_BOT_REPLY)
        return

    # المستويات والخبرة
    new_xp = u.get('xp', 0) + 1
    if new_xp >= u['level'] * 50:
        db.update({'level': u['level']+1, 'xp': 0}, User.id == uid)
        await update.message.reply_text(f"🆙 كفو {name}! وصلت مستوى {u['level']+1}\nلقبك: {config.get_rank_name(u['level']+1)}")
    db.update({'xp': new_xp, 'points': u.get('points',0)+1}, User.id == uid)

    # أوامر البنك الكاملة
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {name}\n📈 لفل: {u['level']}\n💰 رصيدك: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 راتب ملكي: {amt:,}")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")
    elif text in ["زرف", "كنز", "حظ", "استثمار", "مضاربة", "بخشيش"]:
        res = random.randint(-15000000, 40000000)
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 {text}: {res:,}")
    elif text.startswith("هدية "):
        try:
            val = int(text.split()[1])
            if u['balance'] >= val:
                db.update({'balance': u['balance']-val}, User.id == uid)
                await update.message.reply_text(f"🎁 تم إرسال هدية بقيمة {val:,}!")
            else: await update.message.reply_text("❌ رصيدك غير كافٍ!")
        except: pass

    # الروليت (صلاحية المشرفين فقط)
    elif text == "روليت":
        stat = await context.bot.get_chat_member(chat_id, uid)
        if uid == config.OWNER_ID or stat.status in ['creator', 'administrator']:
            context.chat_data['r_on'], context.chat_data['r_p'], context.chat_data['r_s'] = True, [], uid
            await update.message.reply_text(royal.MSG_ROULETTE_START)
        else: await update.message.reply_text("⚠️ الروليت للمدراء فقط!")

    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_p'].append({'id': uid, 'name': name})
        await update.message.reply_text(royal.MSG_ROULETTE_JOIN)
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data['r_s'] or uid == config.OWNER_ID:
            res = await royal.process_roulette_winner(context.chat_data['r_p'])
            if res:
                await update.message.reply_text(royal.MSG_ROULETTE_WIN.format(name=res['name'], wins=res['wins']))
                if res['is_king']: await update.message.reply_text(royal.MSG_ROULETTE_KING.format(name=res['name'], wins=res['wins']))
            context.chat_data['r_on'] = False

    # ملك التفاعل
    elif text == "ملك التفاعل":
        await update.message.reply_text(await royal.get_top_active())

    # تشغيل الألعاب (نص + زر)
    clean = text.replace("لعبة ", "")
    if clean in games.ALL_QUESTIONS or clean in ["تخمين", "صيد"]:
        q, a = await games.get_game_data(clean) if clean in games.ALL_QUESTIONS else (None, None)
        if clean == "تخمين": q, a = "🎲 خمن رقم (1-10)", str(random.randint(1, 10))
        if clean == "صيد": a = str(random.randint(1000, 9999)); q = f"🎯 اكتب الرقم: `{a}`"
        if q:
            context.chat_data['ans'] = a
            await update.message.reply_text(f"🎮 بدأت {clean}:\n{q}")

    # تحقق الإجابة
    if context.chat_data.get('ans') and text.lower() == context.chat_data['ans'].lower():
        context.chat_data['ans'] = None
        db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ كفو {name}! فزت بـ 10 مليون")

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.run_polling()

if __name__ == '__main__': main()
