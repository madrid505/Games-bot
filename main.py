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

# قاعدة البيانات لحفظ الأرصدة والبيانات
db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- دالة فحص الصلاحيات والمجموعات ---
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
    except:
        is_admin = False
    return True, is_owner, is_admin

# --- دالة جلب البيانات أو إنشائها تلقائياً ---
async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_data = db.get(User.id == user_id)
    
    if not user_data:
        # تحديد الرصيد حسب الرتبة عند أول تفاعل
        is_allowed, is_owner, is_admin = await check_auth(update, context)
        if is_owner:
            balance = 500000000000
        elif is_admin:
            balance = 100000000000
        else:
            balance = 10000000000
            
        db.insert({
            'id': user_id, 
            'name': update.effective_user.first_name,
            'balance': balance, 
            'last_salary': 0, 
            'last_tip': 0, 
            'last_rob': 0
        })
        user_data = db.get(User.id == user_id)
    return user_data

# --- معالج الأوامر والرسائل ---
async def handle_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    allowed, is_owner, is_admin = await check_auth(update, context)
    if not allowed: return

    # جلب بيانات المستخدم (تلقائياً حسب رتبته)
    user_data = await get_user_data(update, context)
    current_time = time.time()

    # 1. أوامر البنك
    if text == "رصيدي":
        await update.message.reply_text(f"👤 العضو: {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال")
        return

    if text == "راتب":
        if current_time - user_data.get('last_salary', 0) > 1200: # 20 دقيقة
            amount = random.randint(500000, 2000000)
            db.update({'balance': user_data['balance'] + amount, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 {user_name} استلمت راتبك: {amount:,} ريال")
        else:
            await update.message.reply_text(f"⏳ {user_name}، الراتب كل 20 دقيقة!")
        return

    if text == "بخشيش":
        if current_time - user_data.get('last_tip', 0) > 600: # 10 دقائق
            amount = random.randint(100000, 500000)
            db.update({'balance': user_data['balance'] + amount, 'last_tip': current_time}, User.id == user_id)
            await update.message.reply_text(f"🧧 {user_name} استلمت بخشيش: {amount:,} ريال")
        else:
            await update.message.reply_text(f"⏳ {user_name}، البخشيش كل 10 دقائق!")
        return

    # 2. أوامر الإدارة
    if text == "فتح" and (is_owner or is_admin):
        context.chat_data['games_status'] = 'open'
        await update.message.reply_text("✅ تم فتح الألعاب!")
        return

    if text == "قفل" and (is_owner or is_admin):
        context.chat_data['games_status'] = 'closed'
        await update.message.reply_text("🔒 تم قفل الألعاب.")
        return

    if text.startswith("هدية") and is_owner:
        try:
            amount = int(text.split()[1])
            for u in db.all():
                db.update({'balance': u['balance'] + amount}, User.id == u['id'])
            await update.message.reply_text(f"🎁 كفو! المالك وزّع {amount:,} ريال هدية للجميع!")
        except: pass
        return

    # 3. الألعاب
    if text == "لعبة":
        if context.chat_data.get('games_status') != 'open':
            return await update.message.reply_text("🚫 الألعاب مقفلة.")
        word = random.choice(["برمجة", "مملكة", "صقر", "تقنية", "بنك"])
        context.chat_data['game_active'] = 'fast'
        context.chat_data['target'] = word
        await update.message.reply_text(f"🚀 أسرع واحد يكتب:\n`{word}`", parse_mode='MarkdownV2')
        return

    # التحقق من الفوز بالألعاب
    if context.chat_data.get('game_active') and text == context.chat_data.get('target'):
        context.chat_data['game_active'] = None
        reward = 1000000
        db.update({'balance': user_data['balance'] + reward}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! كتبت الكلمة صح وفزت بمليون ريال!")

# --- تشغيل البوت ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🏦 بوت البنك والألعاب يعمل!")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main))
    print("🚀 البوت يعمل بالكامل مع حفظ البيانات...")
    app.run_polling()

if __name__ == '__main__':
    main()
