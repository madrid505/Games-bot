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

# قاعدة البيانات (حفظ الأرصدة والبيانات)
db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- بيانات لعبة الصور (نماذج متنوعة وقابلة للزيادة) ---
# يمكنك إضافة روابط صورك الخاصة هنا لاحقاً
IMAGE_QUIZ = [
    {"url": "https://bit.ly/3S8fW1u", "answer": "سبونج بوب"},
    {"url": "https://bit.ly/48GvE7G", "answer": "توم وجيري"},
    {"url": "https://bit.ly/3U1E6nJ", "answer": "ماكدونالدز"},
    {"url": "https://bit.ly/3O5xT2y", "answer": "ميسي"},
    {"url": "https://bit.ly/3vL9Y3e", "answer": "بيتزا"},
    {"url": "https://bit.ly/3S7mB2k", "answer": "بيبسي"},
    {"url": "https://bit.ly/496zF8u", "answer": "تويوتا"},
    {"url": "https://bit.ly/3Ue9D8R", "answer": "بينوكيو"},
    {"url": "https://bit.ly/47PzX2m", "answer": "باريس"},
    {"url": "https://bit.ly/3ScX9mG", "answer": "اندومي"}
]

# --- نظام التحقق من الصلاحيات ---
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

# --- جلب بيانات المستخدم تلقائياً ---
async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        allowed, is_owner, is_admin = await check_auth(update, context)
        # توزيع الأرصدة حسب طلبك
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({
            'id': user_id, 'name': update.effective_user.first_name,
            'balance': balance, 'last_salary': 0, 'last_tip': 0, 
            'last_rob': 0, 'last_treasure': 0, 'stolen_total': 0
        })
        user_data = db.get(User.id == user_id)
    return user_data

# --- معالج الأوامر الرئيسي ---
async def handle_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    allowed, is_owner, is_admin = await check_auth(update, context)
    if not allowed: return
    user_data = await get_user_data(update, context)

    # --- أوامر البنك والمعلومات ---
    if text == "رصيدي":
        return await update.message.reply_text(f"👤 الاسم: {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال")

    if text == "حسابي":
        return await update.message.reply_text(f"🏦 رقم حسابك البنكي: `{user_id}`", parse_mode='Markdown')

    if text == "راتب":
        if current_time - user_data.get('last_salary', 0) > 1200:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': user_data['balance'] + amt, 'last_salary': current_time}, User.id == user_id)
            return await update.message.reply_text(f"💵 {user_name} استلمت راتبك: {amt:,} ريال")
        return await update.message.reply_text("⏳ الراتب متاح كل 20 دقيقة!")

    if text == "كنز":
        if current_time - user_data.get('last_treasure', 0) > 3600:
            amt = random.randint(50000000, 200000000)
            db.update({'balance': user_data['balance'] + amt, 'last_treasure': current_time}, User.id == user_id)
            return await update.message.reply_text(f"💎 يا حظك! لقيت كنز فيه: {amt:,} ريال")
        return await update.message.reply_text("⏳ يمكنك البحث عن كنز كل ساعة!")

    if text == "زرف":
        if current_time - user_data.get('last_rob', 0) > 600:
            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 10000000]
            if not others: return await update.message.reply_text("❌ لا يوجد ضحية لزرفها حالياً!")
            target = random.choice(others)
            amt = random.randint(1000000, int(target['balance'] * 0.03))
            db.update({'balance': user_data['balance'] + amt, 'last_rob': current_time, 'stolen_total': user_data.get('stolen_total', 0) + amt}, User.id == user_id)
            db.update({'balance': target['balance'] - amt}, User.id == target['id'])
            return await update.message.reply_text(f"🥷 كفو! زرفت {amt:,} ريال من {target['name']}")
        return await update.message.reply_text("⏳ الزرف متاح كل 10 دقائق!")

    # --- أوامر الإدارة ---
    if text == "فتح" and (is_owner or is_admin):
        context.chat_data['status'] = 'open'
        return await update.message.reply_text("✅ تم فتح الألعاب في المجموعة!")

    if text == "قفل" and (is_owner or is_admin):
        context.chat_data['status'] = 'closed'
        return await update.message.reply_text("🔒 تم قفل الألعاب.")

    if text.startswith("هدية") and is_owner:
        try:
            gift = int(text.split()[1])
            for u in db.all(): db.update({'balance': u['balance'] + gift}, User.id == u['id'])
            return await update.message.reply_text(f"🎁 المالك وزّع هدية {gift:,} لكل المشتركين بالبنك!")
        except: pass

    # --- لعبة الصور ---
    if text == "صورة":
        if context.chat_data.get('status') != 'open': 
            return await update.message.reply_text("🚫 الألعاب مقفلة حالياً من قبل الإدارة.")
        item = random.choice(IMAGE_QUIZ)
        context.chat_data['game_type'] = 'image'
        context.chat_data['correct_ans'] = item['answer']
        return await update.message.reply_photo(photo=item['url'], caption="🖼 عرفت وش في الصورة؟ أسرع واحد يكتب الحل يربح 10 مليون!")

    # --- التحقق من إجابات الألعاب ---
    if context.chat_data.get('game_type') == 'image' and text == context.chat_data.get('correct_ans'):
        context.chat_data['game_type'] = None # إنهاء اللعبة
        reward = 10000000
        db.update({'balance': user_data['balance'] + reward}, User.id == user_id)
        return await update.message.reply_text(f"🎉 كفو {user_name}! إجابتك صحيحة، فزت بـ {reward:,} ريال! ✅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    # معالج الرسائل المباشرة
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main))
    # أمر البداية
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🏦 بوت البنك ولعبة الصور مفعّل!")))
    print("🚀 البوت يعمل بالكامل بدون روليت...")
    app.run_polling()

if __name__ == '__main__': main()
