import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- الإعدادات ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- قائمة الصور ---
IMAGE_QUIZ = [
    {"url": "https://bit.ly/3S8fW1u", "answer": "سبونج بوب"},
    {"url": "https://bit.ly/48GvE7G", "answer": "توم وجيري"},
    {"url": "https://bit.ly/3U1E6nJ", "answer": "ماكدونالدز"},
    {"url": "https://bit.ly/3O5xT2y", "answer": "ميسي"},
    {"url": "https://bit.ly/3vL9Y3e", "answer": "بيتزا"}
]

# --- التحقق من الرتبة ---
async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user: return False, False, False
    user_id = update.effective_user.id
    is_owner = (user_id == OWNER_ID)
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except: is_admin = False
    return True, is_owner, is_admin

# --- نظام البيانات ---
async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        _, is_owner, is_admin = await check_auth(update, context)
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'last_salary': 0, 'last_tip': 0, 'last_rob': 0, 'last_treasure': 0})
        user_data = db.get(User.id == user_id)
    return user_data

# --- المعالج الرئيسي ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    # التأكد من المجموعة المسموحة
    if update.effective_chat.id not in ALLOWED_GROUPS: return

    allowed, is_owner, is_admin = await check_auth(update, context)
    user_data = await get_user_data(update, context)

    # زيادة النقاط تلقائياً
    db.update({'points': user_data.get('points', 0) + 1}, User.id == user_id)

    # --- أوامر المعلومات ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال\n⭐ نقاطك: {user_data.get('points', 0)}")
        return

    # --- أوامر كسب المال ---
    if text == "راتب":
        if current_time - user_data.get('last_salary', 0) > 1200:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': user_data['balance'] + amt, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الراتب متاح كل 20 دقيقة")
        return

    if text == "كنز":
        if current_time - user_data.get('last_treasure', 0) > 3600:
            amt = random.randint(50000000, 200000000)
            db.update({'balance': user_data['balance'] + amt, 'last_treasure': current_time}, User.id == user_id)
            await update.message.reply_text(f"💎 مبروك وجدت كنزاً: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الكنز متاح كل ساعة")
        return

    if text == "زرف":
        if current_time - user_data.get('last_rob', 0) > 600:
            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 10000000]
            if others:
                target = random.choice(others)
                amt = random.randint(1000000, int(target['balance'] * 0.03))
                db.update({'balance': user_data['balance'] + amt, 'last_rob': current_time}, User.id == user_id)
                db.update({'balance': target['balance'] - amt}, User.id == target['id'])
                await update.message.reply_text(f"🥷 زرفت {amt:,} من {target['name']}")
            else: await update.message.reply_text("❌ لا يوجد ضحية غني حالياً")
        else: await update.message.reply_text("⏳ الزرف كل 10 دقائق")
        return

    # --- أوامر الإدارة ---
    if text == "فتح الالعاب" or text == "فتح":
        if is_owner or is_admin:
            context.chat_data['g_active'] = True
            await update.message.reply_text("✅ تم فتح الألعاب")
        return

    if text == "قفل الالعاب" or text == "قفل":
        if is_owner or is_admin:
            context.chat_data['g_active'] = False
            await update.message.reply_text("🔒 تم قفل الألعاب")
        return

    if text == "ملك التفاعل" and (is_owner or is_admin):
        all_u = db.all()
        if all_u:
            top = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥 ملك التفاعل 🔥🔥\n\nالملك: {top['name']}\nالنقاط: {top['points']}\nID: {top['id']}\n\n🏆 مبارك يا اسطورة")
            for u in all_u: db.update({'points': 0}, User.id == u['id'])
        return

    # --- الألعاب (الروليت والصور) ---
    if text == "روليت":
        if is_owner or is_admin:
            context.chat_data['r_on'] = True
            context.chat_data['r_players'] = []
            context.chat_data['r_starter'] = user_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\nلقد بدأ الروليت.. اكتب (انا) للاشتراك")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥 لقد تم تسجيلك يا بطل")
        return

    if text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or is_owner:
            players = context.chat_data.get('r_players', [])
            if players:
                winner = random.choice(players)
                w_data = db.get(User.id == winner['id'])
                db.update({'points': w_data.get('points', 0) + 1}, User.id == winner['id'])
                await update.message.reply_text(f"👑 مباااارك عليك الفوز 👑\n\n👑 {winner['name']} 👑")
            context.chat_data['r_on'] = False
        return

    if text == "صورة" or text == "الصورة":
        if context.chat_data.get('g_active'):
            item = random.choice(IMAGE_QUIZ)
            context.chat_data['img_ans'] = item['answer']
            await update.message.reply_photo(photo=item['url'], caption="🖼 وش في الصورة؟")
        else: await update.message.reply_text("🚫 الألعاب مقفلة")
        return

    # التحقق من إجابة الصورة
    if context.chat_data.get('img_ans') and text == context.chat_data.get('img_ans'):
        context.chat_data['img_ans'] = None
        db.update({'balance': user_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! إجابة صحيحة وفزت بـ 10 مليون")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
