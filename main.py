import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# قاعدة البيانات لحفظ الأرصدة
db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- دالة فحص الصلاحيات ---
async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user: return False, False, False
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if update.effective_chat.type in ["group", "supergroup"] and chat_id not in ALLOWED_GROUPS:
        await context.bot.leave_chat(chat_id)
        return False, False, False
    is_owner = (user_id == OWNER_ID)
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except: is_admin = False
    return True, is_owner, is_admin

# --- دالة جلب/إنشاء البيانات تلقائياً حسب الرتبة ---
async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        allowed, is_owner, is_admin = await check_auth(update, context)
        if is_owner: balance = 500000000000
        elif is_admin: balance = 100000000000
        else: balance = 10000000000
        db.insert({
            'id': user_id, 'name': update.effective_user.first_name,
            'balance': balance, 'last_salary': 0, 'last_tip': 0, 
            'last_rob': 0, 'last_treasure': 0, 'stolen_total': 0
        })
        user_data = db.get(User.id == user_id)
    return user_data

# --- معالج الأوامر والرسائل الرئيسي ---
async def handle_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    allowed, is_owner, is_admin = await check_auth(update, context)
    if not allowed: return

    user_data = await get_user_data(update, context)

    # --- أوامر البنك الجديدة ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 الاسم: {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال")

    elif text == "راتب":
        if current_time - user_data.get('last_salary', 0) > 1200: # 20 دقيقة
            amount = random.randint(5000000, 20000000)
            db.update({'balance': user_data['balance'] + amount, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 {user_name} استلمت راتبك: {amount:,} ريال")
        else: await update.message.reply_text("⏳ الراتب متاح كل 20 دقيقة!")

    elif text == "كنز":
        if current_time - user_data.get('last_treasure', 0) > 3600: # كل ساعة
            amount = random.randint(50000000, 200000000)
            db.update({'balance': user_data['balance'] + amount, 'last_treasure': current_time}, User.id == user_id)
            await update.message.reply_text(f"💎 يا بختك! لقيت كنز فيه: {amount:,} ريال")
        else: await update.message.reply_text("⏳ البحث عن كنز متاح كل ساعة واحدة!")

    elif text == "بخشيش":
        if current_time - user_data.get('last_tip', 0) > 600: # 10 دقائق
            amount = random.randint(1000000, 5000000)
            db.update({'balance': user_data['balance'] + amount, 'last_tip': current_time}, User.id == user_id)
            await update.message.reply_text(f"🧧 استلمت بخشيش: {amount:,} ريال")
        else: await update.message.reply_text("⏳ البخشيش كل 10 دقائق!")

    elif text.startswith("تحويل"):
        try:
            target_id = int(text.split()[1])
            amount = int(text.split()[2])
            if user_data['balance'] < amount: return await update.message.reply_text("❌ رصيدك لا يكفي!")
            target_data = db.get(User.id == target_id)
            if not target_data: return await update.message.reply_text("❌ الحساب غير مسجل.")
            db.update({'balance': user_data['balance'] - amount}, User.id == user_id)
            db.update({'balance': target_data['balance'] + amount}, User.id == target_id)
            await update.message.reply_text(f"✅ تم تحويل {amount:,} إلى {target_data['name']}")
        except: await update.message.reply_text("⚠️ استعمل: تحويل (رقم الحساب) (المبلغ)")

    elif text == "زرف":
        if current_time - user_data.get('last_rob', 0) > 600:
            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 10000000]
            if not others: return await update.message.reply_text("❌ لا يوجد ضحية غني حالياً!")
            target = random.choice(others)
            amount = random.randint(1000000, int(target['balance'] * 0.03))
            db.update({'balance': user_data['balance'] + amount, 'last_rob': current_time, 'stolen_total': user_data.get('stolen_total', 0) + amount}, User.id == user_id)
            db.update({'balance': target['balance'] - amount}, User.id == target['id'])
            await update.message.reply_text(f"🥷 كفو! زرفت {amount:,} من {target['name']}")
        else: await update.message.reply_text("⏳ تقدر تزرف كل 10 دقائق!")

    elif text.startswith("استثمار"):
        try:
            amount = int(text.split()[1])
            if user_data['balance'] < amount: return await update.message.reply_text("❌ رصيدك لا يكفي!")
            profit_percent = random.randint(1, 15)
            profit = int(amount * (profit_percent / 100))
            db.update({'balance': user_data['balance'] + profit}, User.id == user_id)
            await update.message.reply_text(f"📈 استثمار ناجح! ربحت {profit_percent}% (صافي: {profit:,} ريال)")
        except: await update.message.reply_text("⚠️ استعمل: استثمار (المبلغ)")

    elif text.startswith("حظ"):
        try:
            bet = int(text.split()[1])
            if user_data['balance'] < bet: return await update.message.reply_text("❌ رصيدك قليل!")
            if random.random() > 0.5:
                db.update({'balance': user_data['balance'] + bet}, User.id == user_id)
                await update.message.reply_text(f"🔥 فزت! تدبل المبلغ: {bet*2:,}")
            else:
                db.update({'balance': user_data['balance'] - bet}, User.id == user_id)
                await update.message.reply_text("📉 طار الحظ وخسرت!")
        except: pass

    elif text == "توب الفلوس":
        top = sorted(db.all(), key=lambda x: x['balance'], reverse=True)[:10]
        msg = "💰 **قائمة الأغنياء:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i}- {u['name']} : {u['balance']:,}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif text.startswith("هدية") and is_owner:
        try:
            gift = int(text.split()[1])
            for u in db.all(): db.update({'balance': u['balance'] + gift}, User.id == u['id'])
            await update.message.reply_text(f"🎁 كفو! المالك وزّع هدية {gift:,} للجميع!")
        except: pass

    # --- أوامر الإدارة والألعاب ---
    if text == "فتح" and (is_owner or is_admin):
        context.chat_data['games_status'] = 'open'
        await update.message.reply_text("✅ تم فتح الألعاب!")
    elif text == "قفل" and (is_owner or is_admin):
        context.chat_data['games_status'] = 'closed'
        await update.message.reply_text("🔒 تم قفل الألعاب.")

    if text == "لعبة":
        if context.chat_data.get('games_status') != 'open': return await update.message.reply_text("🚫 الألعاب مقفلة.")
        word = random.choice(["برمجة", "مملكة", "صقر", "تقنية", "بنك"])
        context.chat_data['game_active'] = 'fast'
        context.chat_data['target'] = word
        await update.message.reply_text(f"🚀 أسرع واحد يكتب:\n`{word}`", parse_mode='MarkdownV2')

    if context.chat_data.get('game_active') and text == context.chat_data.get('target'):
        context.chat_data['game_active'] = None
        db.update({'balance': user_data['balance'] + 5000000}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! فزت بـ 5 مليون!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main))
    print("🚀 البوت المطور يعمل الآن...")
    app.run_polling()

if __name__ == '__main__': main()
