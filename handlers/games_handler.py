import random
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS

# تحميل جميع الأسئلة
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
        [InlineKeyboardButton("💰 رصيدي", callback_data="cmd_balance"), InlineKeyboardButton("🏆 المتصدرين", callback_data="cmd_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # --- نظام ملك التفاعل (تحديث العداد) ---
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == user_id)
    
    if current_msgs >= 1000: # مثال: ملك التفاعل عند 1000 رسالة
        await update.message.reply_text(
            f"👑👑👑 **ملك التفاعل الجديد** 👑👑👑\n\n"
            f"تهانينا للأسطورة \" {user_name} \"\n"
            f"لقد تربعت على عرش التفاعل بـ {current_msgs} رسالة!\n"
            f"تم منحك وسام الاستحقاق ولقب ملك التفاعل 🔥"
        )
        db.update({'msg_count': 0}, User.id == user_id) # تصفير بعد اللقب أو حسب نظامك

    # --- القائمة الرئيسية ---
    if text in ["قائمة", "الاوامر", "الأوامر", "/start", "يا بوت"]:
        await update.message.reply_text(
            f"👑 **أهلاً بك يا أسطورة في عالم مونوبولي العظيم** 👑\n\n"
            f"يا {user_name}، إليك لوحة التحكم الشاملة:\n",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    # --- التحقق من الإجابات ---
    correct_answer = context.chat_data.get('game_ans')
    if correct_answer and text == correct_answer:
        reward = 50000
        new_balance = u_data.get('balance', 0) + reward
        db.update({'balance': new_balance, 'points': u_data.get('points', 0) + 1}, User.id == user_id)
        await update.message.reply_text(f"✅ **إجابة صحيحة يا بطل!**\n\n👤 الفائز: {user_name}\n💰 الجائزة: {reward:,} دينار")
        context.chat_data['game_ans'] = None
        return

    # --- أوامر البنك الملكية ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي المركزي**\n👤 الاسم: {user_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
    
    elif text == "توب":
        top_10 = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top_10, 1): msg += f"{i} - {u['name']} 💰 ({u['balance']:,} د)\n"
        await update.message.reply_text(msg)

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            salary = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + salary, 'last_salary': now}, User.id == user_id)
            await update.message.reply_text(f"💵 **مبروك!** تم إيداع راتبك وقدره {salary:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ باقي {rem} دقيقة لراتبك القادم.")

    elif text == "زرف" and update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        t_db = db.get(User.id == target_id)
        if t_db and t_db.get('balance', 0) > 100000:
            if random.random() < 0.25:
                stolen = random.randint(50000, int(t_db['balance'] * 0.05))
                db.update({'balance': t_db['balance'] - stolen}, User.id == target_id)
                db.update({'balance': u_data['balance'] + stolen}, User.id == user_id)
                await update.message.reply_text(f"🥷 **ذيب!** زرفت {stolen:,} دينار من {t_db['name']}!")
            else:
                db.update({'balance': max(0, u_data['balance'] - 100000)}, User.id == user_id)
                await update.message.reply_text("👮 **مسكتك الشرطة!** دفعت غرامة 100 ألف دينار.")

    elif text == "كنز":
        if random.random() < 0.08:
            treasure = random.randint(10000000, 50000000)
            db.update({'balance': u_data['balance'] + treasure}, User.id == user_id)
            await update.message.reply_text(f"🏴‍☠️ **يا حظك!** لقيت كنز قيمته {treasure:,} دينار!")
        else: await update.message.reply_text("🏜️ لم تجد شيئاً في رحلة البحث..")

    # --- نظام الروليت الملكي الأصلي ---
    if text == "روليت":
        admins = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if user_id == OWNER_ID or user_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 اكتب **انا** للاشتراك 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == user_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': user_id, 'name': user_name})

    elif text == "تم" and context.chat_data.get('r_on') and user_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            w_db = db.get(User.id == win['id'])
            new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_w}, User.id == win['id'])
            await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_w} )")
            if new_w >= 5:
                await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n👑 \" {win['name']} \" 👑\n🔥🔥 تم تصفير نقاط الجميع 🔥🔥")
                for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
        context.chat_data['r_on'] = False

    # --- تشغيل الألعاب (نصوص وصور) ---
    elif text in QUESTIONS:
        q_data = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q_data['answer']
        cap = f"🎮 بدأت {text}:\n\n【 {q_data['question']} 】"
        if q_data.get('image') and os.path.exists(q_data['image']):
            await update.message.reply_photo(photo=open(q_data['image'], 'rb'), caption=cap)
        else: await update.message.reply_text(cap)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            cap = f"🎮 بدأت {game} (عبر القائمة):\n【 {q['question']} 】"
            if q.get('image') and os.path.exists(q['image']):
                await query.message.reply_photo(photo=open(q['image'], 'rb'), caption=cap)
            else: await query.message.reply_text(cap)
    elif query.data == "cmd_balance":
        u = db.get(User.id == user_id)
        await query.message.reply_text(f"💰 رصيدك الحالي: {u['balance']:,} دينار.")
    elif query.data == "cmd_top":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **هوامير مونوبولي:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u['name']} ({u['balance']:,})\n"
        await query.message.reply_text(msg)
