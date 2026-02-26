import random
import os
import time
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS

# تحميل الألعاب
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
        [InlineKeyboardButton("💰 الرصيد", callback_data="cmd_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="cmd_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تجاهل الرسائل خارج الجروبات المسموحة أو الرسائل الفارغة
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    
    # جلب بيانات المستخدم (تلقائياً تنشئ حساب إذا لم يوجد)
    u_data = await get_user_data(update)

    # --- 🏆 1. ملك التفاعل (تحديث العداد) ---
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)
    
    # طباعة في اللوج لمراقبة التفاعل
    logging.info(f"📈 تفاعل: {u_name} وصل إلى {current_msgs} رسالة")

    if current_msgs >= 1000:
        await update.message.reply_text(
            f"🔥🔥🔥 **ملك التفاعل** 🔥🔥\n\n"
            f"اسم الملك : {u_name}\n"
            f"عدد المشاركات : {current_msgs}\n\n"
            f"🔥🔥 مبارك الفوز يا اسطورة القروب 🔥🔥"
        )
        db.update({'msg_count': 0}, User.id == u_id)

    # --- 🏦 2. أوامر البنك ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي**\n👤: {u_name}\n💰: {u_data['balance']:,} د\n🏆: {u_data['points']} ن")
        return

    elif text == "توب":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير:**\n\n"
        for i, u in enumerate(top, 1):
            msg += f"{i} - {u.get('name', 'لاعب')} ({u.get('balance', 0):,} د)\n"
        await update.message.reply_text(msg)
        return

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            sal = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + sal, 'last_salary': now}, User.id == u_id)
            await update.message.reply_text(f"💵 تم صرف راتبك وقدره {sal:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ ارجع بعد {rem} دقيقة.")
        return

    elif text == "بخشيش":
        tip = random.randint(50000, 150000)
        db.update({'balance': u_data['balance'] + tip}, User.id == u_id)
        await update.message.reply_text(f"🎁 استلمت {tip:,} دينار بخشيش.")
        return

    elif text == "زرف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if target.is_bot: return
        t_data = db.get(User.id == target.id)
        if t_data and t_data.get('balance', 0) > 100000:
            amt = random.randint(10000, 100000)
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            db.update({'balance': t_data['balance'] - amt}, User.id == target.id)
            await update.message.reply_text(f"🥷 زرفت {amt:,} من {target.first_name}!")
        else:
            await update.message.reply_text("❌ ما عنده شي تزرفه!")
        return

    # --- 🎰 3. الروليت ---
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 بدأت الروليت! اكتب 'انا' للاشتراك.")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == u_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
            await update.message.reply_text(f"📢 {u_name} تم تسجيلك!")
        return

    if text == "تم" and context.chat_data.get('r_on') and u_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            await update.message.reply_text(f"👑 الفائز بالروليت هو: {win['name']}!")
        context.chat_data['r_on'] = False
        return

    # --- 🎲 4. الألعاب ---
    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text("👑 قائمة عالم مونوبولي:", reply_markup=get_main_menu_keyboard())
        return

    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ كفو {u_name}! فزت بـ 50 ألف.")
        context.chat_data['game_ans'] = None
        return

    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        await update.message.reply_text(f"🎮 {text}:\n【 {q['question']} 】")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            await query.message.reply_text(f"🎮 {game}:\n【 {q['question']} 】")
