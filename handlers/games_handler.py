import random
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS

# تحميل الـ 13 لعبة بالكامل
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
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # --- 🏆 نظام ملك التفاعل (تحديث العداد والرسالة الملكية) ---
    msg_count = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': msg_count}, User.id == user_id)
    
    if msg_count >= 1000:
        await update.message.reply_text(
            f"🔥🔥🔥 **ملك التفاعل** 🔥🔥\n\n"
            f"اسم الملك : {user_name}\n"
            f"عدد النقاط : {u_data.get('points', 0)}\n"
            f"عدد المشاركات : {msg_count}\n\n"
            f"🔥🔥 مبارك الفوز يا اسطورة القروب 🔥🔥"
        )
        db.update({'msg_count': 0}, User.id == user_id)

    # --- 🏦 أوامر البنك الملكية الشاملة ---
    # 1. الرصيد والتوب
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي المركزي**\n👤 الاسم: {user_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
        return
    elif text == "توب":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u['name']} ({u['balance']:,})\n"
        await update.message.reply_text(msg)
        return

    # 2. الراتب، البخسيس، الهدية
    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            s = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + s, 'last_salary': now}, User.id == user_id)
            await update.message.reply_text(f"💵 **المرسوم الملكي:** تم صرف راتبك {s:,} دينار.")
        else: await update.message.reply_text(f"⏳ الراتب لم ينزل بعد.")
        return

    elif text == "بخشيش":
        tip = random.randint(10000, 50000)
        db.update({'balance': u_data['balance'] + tip}, User.id == user_id)
        await update.message.reply_text(f"🎁 تفضل يا ملك، بخشيش {tip:,} دينار من الإدارة.")
        return

    elif text.startswith("هدية") and update.message.reply_to_message:
        try:
            amt = int(text.split()[1])
            target_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= amt > 0:
                t_data = await get_user_data(update.message.reply_to_message)
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                db.update({'balance': t_data['balance'] + amt}, User.id == target_id)
                await update.message.reply_text(f"🎁 تم إرسال هدية بقيمة {amt:,} دينار إلى {update.message.reply_to_message.from_user.first_name}.")
            else: await update.message.reply_text("❌ رصيدك لا يكفي.")
        except: await update.message.reply_text("⚠️ اكتب: هدية + المبلغ (بالرد على الشخص).")
        return

    # 3. استثمار، حظ، مضاربة، زرف
    elif text == "حظ":
        win = random.choice([True, False])
        amt = random.randint(100000, 500000)
        if win:
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            await update.message.reply_text(f"🎰 حظك ذهب! فزت بـ {amt:,} دينار.")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == user_id)
            await update.message.reply_text(f"📉 للأسف، خسرت {amt:,} دينار.")
        return

    # --- 🎰 الروليت الملكي المصحح ---
    if text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        context.chat_data['r_ana_counts'] = {} # لحساب كم مرة كتب كل عضو "انا"
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 اكتب انا للاشتراك 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        # زيادة عدد المشاركات (كم مرة كتب انا)
        context.chat_data['r_ana_counts'][user_id] = context.chat_data['r_ana_counts'].get(user_id, 0) + 1
        if not any(p['id'] == user_id for p in context.chat_data['r_players']):
            context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on') and user_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            w_db = db.get(User.id == win['id'])
            new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_w}, User.id == win['id'])
            
            await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_w} )\n👈👈 استمر معنا حتى الجائزة الكبرى 👉👉")
            
            if new_w >= 5:
                ana_count = context.chat_data['r_ana_counts'].get(win['id'], 0)
                await update.message.reply_text(
                    f"👑👑👑 ملك الروليت 👑👑👑\n\n"
                    f"             👑 \" {win['name']} \" 👑\n\n"
                    f"       🔥🔥 \"5 نقاط\"🔥🔥\n"
                    f"👈👈 \"{ana_count} مشاركات\"👉👉"
                )
                for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
        context.chat_data['r_on'] = False

    # --- 🎮 الألعاب الـ 13 ---
    elif text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        cap = f"🎮 بدأت {text}:\n【 {q['question']} 】"
        if q.get('image') and os.path.exists(q['image']):
            await update.message.reply_photo(photo=open(q['image'], 'rb'), caption=cap)
        else: await update.message.reply_text(cap)

    # التحقق من إجابة الألعاب
    elif context.chat_data.get('game_ans') and text == context.chat_data['game_ans']:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو! فزت بـ 50,000 دينار.")
        context.chat_data['game_ans'] = None

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # (كود الـ Callback يبقى ثابتاً لربط الأزرار بالألعاب أعلاه)
    pass
