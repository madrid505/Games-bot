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
    # 1. التأكد من وجود رسالة
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # 2. التحقق من الجروب (تأكد أن الـ ID موجود في config.py)
    if chat_id not in GROUP_IDS:
        print(f"⚠️ جروب غير مسموح: {chat_id}")
        return

    # 3. جلب بيانات المستخدم
    u_data = await get_user_data(update)

    # --- 🏆 نظام ملك التفاعل (تحديث فوري) ---
    # نزيد العداد مع كل رسالة مهما كان محتواها
    new_msg_count = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': new_msg_count}, User.id == u_id)
    
    # طباعة في اللوج للـتأكد (ستراها في Northflank)
    print(f"📊 [تفاعل] {u_name} | العداد: {new_msg_count}")

    if new_msg_count >= 1000:
        await update.message.reply_text(
            f"🔥🔥🔥 **ملك التفاعل** 🔥🔥\n\n"
            f"اسم الملك : {u_name}\n"
            f"عدد النقاط : {u_data.get('points', 0)}\n"
            f"عدد المشاركات : {new_msg_count}\n\n"
            f"🔥🔥 مبارك الفوز يا اسطورة القروب 🔥🔥"
        )
        db.update({'msg_count': 0}, User.id == u_id)

    # --- 🏦 أوامر البنك الملكية ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي المركزي**\n👤 الاسم: {u_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
        return

    elif text == "توب":
        top_list = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top_list, 1):
            msg += f"{i} - {u.get('name', 'لاعب')} ⮕ ({u.get('balance', 0):,} د)\n"
        await update.message.reply_text(msg)
        return

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            salary = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + salary, 'last_salary': now}, User.id == u_id)
            await update.message.reply_text(f"💵 **المرسوم الملكي:** تم إيداع راتبك وقدره {salary:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ **مهلاً يا ملك:** ارجع بعد {rem} دقيقة.")
        return

    elif text == "بخشيش":
        tip = random.randint(50000, 150000)
        db.update({'balance': u_data['balance'] + tip}, User.id == u_id)
        await update.message.reply_text(f"🎁 **بخشيش ملكي:** استلمت {tip:,} دينار.")
        return

    # --- 🎰 الروليت ---
    if text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 بدأت لعبة الروليت، اكتب 'انا' للاشتراك.")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == u_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
            await update.message.reply_text(f"📢 {u_name} تم تسجيلك!")
        return

    # --- 🎲 الألعاب وقائمة الأوامر ---
    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **عالم مونوبولي العظيم** 👑", reply_markup=get_main_menu_keyboard())
        return

    # التحقق من إجابات الألعاب
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **صح!** {u_name} فزت بـ 50,000 دينار ونقطة ملكية.")
        context.chat_data['game_ans'] = None
        return

    if text in QUESTIONS:
        q_data = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q_data['answer']
        await update.message.reply_text(f"🎮 لعبة {text}:\n【 {q_data['question']} 】")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            await query.message.reply_text(f"🎮 بدأت {game}:\n【 {q['question']} 】")
