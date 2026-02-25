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

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- بيانات الصور المتنوعة ---
IMAGE_QUIZ = [
    {"url": "https://bit.ly/3S8fW1u", "answer": "سبونج بوب"},
    {"url": "https://bit.ly/48GvE7G", "answer": "توم وجيري"},
    {"url": "https://bit.ly/3U1E6nJ", "answer": "ماكدونالدز"},
    {"url": "https://bit.ly/3O5xT2y", "answer": "ميسي"},
    {"url": "https://bit.ly/3vL9Y3e", "answer": "بيتزا"}
]

# --- نظام الصلاحيات ---
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

# --- جلب البيانات وتوزيع الرصيد الآلي ---
async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        allowed, is_owner, is_admin = await check_auth(update, context)
        # 500 مليار للمالك، 100 مليار للمشرف، 10 مليار للعضو
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({
            'id': user_id, 'name': update.effective_user.first_name,
            'balance': balance, 'points': 0, 'last_salary': 0, 
            'last_tip': 0, 'last_rob': 0, 'last_treasure': 0
        })
        user_data = db.get(User.id == user_id)
    return user_data

# --- وظيفة إعلان الفائز بملك التفاعل ---
async def announce_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_users = db.all()
    if not all_users: return
    winner = max(all_users, key=lambda x: x.get('points', 0))
    if winner.get('points', 0) == 0:
        return await update.message.reply_text("📉 لا يوجد تفاعل كافٍ حالياً لإعلان ملك الأسبوع.")

    text = (
        "🔥🔥🔥 ملك التفاعل 🔥🔥\n\n"
        f"اسم الملك : {winner['name']}\n\n"
        f"عدد النقاط : {winner['points']}\n\n"
        f"ID : {winner['id']}\n\n"
        "🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥"
    )
    await update.message.reply_text(text)
    # تصفير النقاط للمسابقة الجديدة
    for u in all_users: db.update({'points': 0}, User.id == u['id'])

# --- معالج الرسائل الرئيسي ---
async def handle_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    allowed, is_owner, is_admin = await check_auth(update, context)
    if not allowed: return
    user_data = await get_user_data(update, context)

    # حساب نقاط التفاعل
    db.update({'points': user_data.get('points', 0) + 1}, User.id == user_id)

    # --- الأوامر المباشرة ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {user_data['balance']:,}\n⭐ نقاطك: {user_data.get('points', 0)}")
    
    elif text == "نقاطي":
        await update.message.reply_text(f"⭐ نقاط تفاعلك: {user_data.get('points', 0)}")

    elif text == "ملك التفاعل" and (is_owner or is_admin):
        await announce_winner(update, context)

    elif text == "فتح" and (is_owner or is_admin):
        context.chat_data['status'] = 'open'
        await update.message.reply_text("✅ تم فتح الألعاب!")

    elif text == "صورة":
        if context.chat_data.get('status') != 'open': return await update.message.reply_text("🚫 الألعاب مقفلة.")
        item = random.choice(IMAGE_QUIZ)
        context.chat_data['game'] = 'image'
        context.chat_data['ans'] = item['answer']
        await update.message.reply_photo(photo=item['url'], caption="🖼 وش في الصورة؟")

    # التحقق من إجابة الصورة
    if context.chat_data.get('game') == 'image' and text == context.chat_data.get('ans'):
        context.chat_data['game'] = None
        db.update({'balance': user_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! فزت بـ 10 مليون! ✅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main))
    app.run_polling()

if __name__ == '__main__': main()
