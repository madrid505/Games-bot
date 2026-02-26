import random
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS

# تحميل الـ 13 لعبة
QUESTIONS = load_questions()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="run_islamic"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="run_general")],
        [InlineKeyboardButton("🏎️ سيارات", callback_data="run_cars"), InlineKeyboardButton("⚽ أندية", callback_data="run_clubs")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="run_countries"), InlineKeyboardButton("🚩 أعلام", callback_data="run_flags")],
        [InlineKeyboardButton("🔄 عكس", callback_data="run_reverse"), InlineKeyboardButton("🔡 ترتيب", callback_data="run_order")],
        [InlineKeyboardButton("🧩 تفكيك", callback_data="run_decompose"), InlineKeyboardButton("🧮 رياضيات", callback_data="run_math")],
        [InlineKeyboardButton("🇬🇧 إنجليزي", callback_data="run_english"), InlineKeyboardButton("📝 كلمات", callback_data="run_words")],
        [InlineKeyboardButton("🔍 مختلف", callback_data="run_misc")],
        [InlineKeyboardButton("💰 رصيدي الملكي", callback_data="cmd_balance"), InlineKeyboardButton("🏆 قائمة الهوامير", callback_data="cmd_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # --- 🏆 1. ملك التفاعل (يعمل بصمت مع كل رسالة) ---
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)
    
    if current_msgs >= 1000:
        await update.message.reply_text(
            f"🔥🔥🔥 **ملك التفاعل** 🔥🔥\n\n"
            f"اسم الملك : {u_name}\n"
            f"عدد النقاط : {u_data.get('points', 0)}\n"
            f"عدد المشاركات : {current_msgs}\n\n"
            f"🔥🔥 مبارك الفوز يا اسطورة القروب 🔥🔥"
        )
        db.update({'msg_count': 0}, User.id == u_id)

    # --- 🎰 2. الروليت (شعب مونوبولي العظيم) ---
    if text == "روليت":
        admins = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == u_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")
        return

    if text == "تم" and context.chat_data.get('r_on') and u_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            w_db = db.get(User.id == win['id'])
            new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_w}, User.id == win['id'])
            await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_w} )\n👈👈 استمر معنا حتى الجائزة الكبرى 👉👉")
            if new_w >= 5:
                await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n👑 \" {win['name']} \" 👑\n\n🔥🔥 \"5 نقاط\"🔥🔥")
                for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
        context.chat_data['r_on'] = False
        return

    # --- 🏦 3. أوامر البنك الملكية ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي المركزي**\n👤 الاسم: {u_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
    
    elif text == "توب":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u['name']} ({u['balance']:,} د)\n"
        await update.message.reply_text(msg)

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            salary = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + salary, 'last_salary': now}, User.id == u_id)
            await update.message.reply_text(f"💵 **المرسوم الملكي:** تم إيداع راتبك وقدره {salary:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ ارجع بعد {rem} دقيقة لاستلام الراتب.")

    # --- 🎮 4. الألعاب والتحقق ---
    if text in ["قائمة", "الاوامر", "الأوامر", "/start"]:
        await update.message.reply_text(f"👑 **عالم مونوبولي العظيم** 👑\n\nاختر لعبتك يا بطل:", reply_markup=get_main_menu_keyboard())
        return

    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **كفو يا بطل!**\n\nإجابتك صحيحة وفزت بـ 50,000 دينار ونقطة ملكية!")
        context.chat_data['game_ans'] = None
        return

    if text in QUESTIONS:
        q_data = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q_data['answer']
        cap = f"🎮 بدأت لعبة {text}:\n\n【 {q_data['question']} 】"
        if q_data.get('image') and os.path.exists(q_data['image']):
            await update.message.reply_photo(photo=open(q_data['image'], 'rb'), caption=cap)
        else: await update.message.reply_text(cap)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            cap = f"🎮 بدأت {game}:\n【 {q['question']} 】"
            if q.get('image') and os.path.exists(q['image']):
                await query.message.reply_photo(photo=open(q['image'], 'rb'), caption=cap)
            else: await query.message.reply_text(cap)
    elif query.data == "cmd_balance":
        u = db.get(User.id == query.from_user.id)
        await query.message.reply_text(f"💰 رصيدك: {u['balance']:,} دينار.")
    elif query.data == "cmd_top":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 قائمة الهوامير:\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u['name']} ({u['balance']:,})\n"
        await query.message.reply_text(msg)
