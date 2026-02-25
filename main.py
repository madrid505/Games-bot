import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- قائمة صور جديدة بروابط مباشرة ومضمونة ---
IMAGE_QUIZ = [
    {"url": "https://upload.wikimedia.org/wikipedia/ar/7/77/SpongeBob_SquarePants_characters.png", "answer": "سبونج بوب"},
    {"url": "https://upload.wikimedia.org/wikipedia/en/2/2f/Jerry_Mouse.png", "answer": "جيري"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/McDonald%27s_Golden_Arches.svg/1200px-McDonald%27s_Golden_Arches.svg.png", "answer": "ماكدونالدز"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/b/b8/Messi_vs_Nigeria_2018.jpg", "answer": "ميسي"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/9/91/Pizza-3007395.jpg", "answer": "بيتزا"}
]

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user: return False, False, False
    user_id = update.effective_user.id
    is_owner = (user_id == OWNER_ID)
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except: is_admin = False
    return True, is_owner, is_admin

async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        _, is_owner, is_admin = await check_auth(update, context)
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'last_salary': 0, 'last_rob': 0, 'last_treasure': 0, 'last_luck': 0})
        user_data = db.get(User.id == user_id)
    return user_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return

    allowed, is_owner, is_admin = await check_auth(update, context)
    user_data = await get_user_data(update, context)
    db.update({'points': user_data.get('points', 0) + 1}, User.id == user_id)

    # --- أمر "العاب" ---
    if text in ["العاب", "ألعاب"]:
        games_menu = (
            "🎮 **قائمة ألعاب مونوبولي العظيم** 🎮\n\n"
            "💰 **ألعاب البنك:** (رصيدي، راتب، كنز، زرف، حظ)\n"
            "🎲 **ألعاب التفاعل:** (صورة، روليت، ملك التفاعل)\n"
            "⚙️ **التحكم:** (فتح، قفل)"
        )
        await update.message.reply_text(games_menu, parse_mode="Markdown")
        return

    # --- التحكم ---
    if text in ["فتح", "فتح الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['active'] = True
            await update.message.reply_text("✅ تم فتح الألعاب بنجاح!")
        return

    if text in ["قفل", "قفل الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['active'] = False
            await update.message.reply_text("🔒 تم قفل الألعاب.")
        return

    # --- البنك ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال\n⭐ نقاطك: {user_data.get('points', 0)}")
    
    elif text == "راتب":
        if current_time - user_data.get('last_salary', 0) > 1200:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': user_data['balance'] + amt, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الراتب متاح كل 20 دقيقة")

    elif text == "كنز":
        if current_time - user_data.get('last_treasure', 0) > 3600:
            amt = random.randint(50000000, 200000000)
            db.update({'balance': user_data['balance'] + amt, 'last_treasure': current_time}, User.id == user_id)
            await update.message.reply_text(f"💎 مبروك وجدت كنزاً: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الكنز متاح كل ساعة")

    elif text == "زرف":
        others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 10000000]
        if others:
            target = random.choice(others)
            amt = random.randint(1000000, 5000000)
            db.update({'balance': user_data['balance'] + amt}, User.id == user_id)
            db.update({'balance': target['balance'] - amt}, User.id == target['id'])
            await update.message.reply_text(f"🥷 زرفت {amt:,} من {target['name']}")
        else: await update.message.reply_text("❌ لا يوجد ضحية غني حالياً")

    # --- ملك التفاعل ---
    elif text == "ملك التفاعل" and (is_owner or is_admin):
        all_u = db.all()
        if all_u:
            winner = max(all_u, key=lambda x: x.get('points', 0))
            msg = (f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {winner['name']}\n\nعدد النقاط : {winner['points']}\n\nID : {winner['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            await update.message.reply_text(msg)
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    # --- الروليت ---
    elif text == "روليت":
        if is_owner or is_admin:
            context.chat_data['r_on'] = True
            context.chat_data['r_players'] = []
            context.chat_data['r_starter'] = user_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on'):
        players = context.chat_data.get('r_players', [])
        if players:
            winner = random.choice(players)
            win_msg = (f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {winner['name']} \" 👑\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
            await update.message.reply_text(win_msg)
        context.chat_data['r_on'] = False

    # --- لعبة الصور (إصلاح الروابط والاستجابة) ---
    elif text in ["صورة", "الصورة", "صوره"]:
        if context.chat_data.get('active'):
            try:
                item = random.choice(IMAGE_QUIZ)
                context.chat_data['ans'] = item['answer']
                await update.message.reply_photo(photo=item['url'], caption="🖼 وش في الصورة؟ أسرع واحد يجاوب يربح 10 مليون!")
            except Exception as e:
                logging.error(f"Error sending photo: {e}")
                await update.message.reply_text("⚠️ خلل في جلب الصورة، حاول مرة أخرى.")
        else: await update.message.reply_text("🚫 الألعاب مقفلة.. اطلب من المشرف فتحها")

    elif context.chat_data.get('ans') and text == context.chat_data.get('ans'):
        context.chat_data['ans'] = None
        db.update({'balance': user_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! إجابة صحيحة وفزت بـ 10,000,000 ريال! ✅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
