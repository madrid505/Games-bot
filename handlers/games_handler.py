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

    # --- 🏆 1. نظام ملك التفاعل (تحديث وتوب 10) ---
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)
    
    if text == "ملك التفاعل":
        all_u = db.all()
        top_active = sorted(all_u, key=lambda x: x.get('msg_count', 0), reverse=True)[:10]
        msg = "👑 **قائمة ملوك التفاعل - TOP 10** 👑\n\n"
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(top_active):
            msg += f"{emojis[i]} {user.get('name', 'لاعب')} ⮕ {user.get('msg_count', 0)} مشاركة\n"
        await update.message.reply_text(msg)
        return

    if current_msgs >= 1000:
        await update.message.reply_text(f"🔥🔥🔥 **ملك التفاعل** 🔥🔥\n\nاسم الملك : {u_name}\nعدد النقاط : {u_data.get('points', 0)}\nعدد المشاركات : {current_msgs}\n\n🔥🔥 مبارك الفوز يا اسطورة القروب 🔥🔥")
        db.update({'msg_count': 0}, User.id == u_id)

    # --- 🏦 2. أوامر البنك الشاملة (جميع الأوامر المطلوبة) ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي المركزي**\n👤 الاسم: {u_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
        return

    elif text in ["حظ", "استثمار", "كنز", "مضاربة"]:
        amt = random.randint(100000, 1000000)
        if random.random() > 0.5:
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            await update.message.reply_text(f"📈 **يا ملك الحظ!** ربحت في {text} مبلغ {amt:,} دينار.")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == u_id)
            await update.message.reply_text(f"📉 **للأسف!** خسر رصيدك في {text} مبلغ {amt:,} دينار.")
        return

    elif text in ["توب", "توب الاغنياء"]:
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u.get('name', 'لاعب')} ({u.get('balance', 0):,} د)\n"
        await update.message.reply_text(msg)
        return

    elif text == "توب الحرامية":
        top = sorted(db.all(), key=lambda x: x.get('steal_count', 0), reverse=True)[:10]
        msg = "🥷 **أكبر 10 حرامية (محترفي الزرف):**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u.get('name', 'لاعب')} ({u.get('steal_count', 0)} زرفة)\n"
        await update.message.reply_text(msg)
        return

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            sal = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + sal, 'last_salary': now}, User.id == u_id)
            await update.message.reply_text(f"💵 **مرسوم ملكي:** تم صرف راتب {sal:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ ارجع بعد {rem} دقيقة.")
        return

    elif text == "بخشيش":
        tip = random.randint(50000, 150000)
        db.update({'balance': u_data['balance'] + tip}, User.id == u_id)
        await update.message.reply_text(f"🎁 استلمت بخشيش {tip:,} دينار.")
        return

    elif text == "زرف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        t_data = db.get(User.id == target.id)
        if t_data and t_data.get('balance', 0) > 100000:
            amt = random.randint(10000, 100000)
            db.update({'balance': u_data['balance'] + amt, 'steal_count': u_data.get('steal_count', 0) + 1}, User.id == u_id)
            db.update({'balance': t_data['balance'] - amt}, User.id == target.id)
            await update.message.reply_text(f"🥷 زرفت {amt:,} من {target.first_name}!")
        return

    # --- 🎰 3. نظام الروليت الملكي (مع إعلان ملك الروليت النهائي) ---
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب 'انا' 🌹🌹")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        # السماح بتكرار "انا" للحماس
        await update.message.reply_text(f"📢🔥🌹 لقد تم تسجيلك يا بطل {u_name} 🌹🔥📢")
        if not any(p['id'] == u_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
        return

    if text == "تم" and context.chat_data.get('r_on') and u_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            w_db = db.get(User.id == win['id'])
            new_wins = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_wins}, User.id == win['id'])
            
            # --- 🏆 إعلان ملك الروليت النهائي (عند 5 نقاط) ---
            if new_wins >= 5:
                await update.message.reply_text(
                    f"✨✨✨✨✨✨✨✨✨✨✨✨\n"
                    f"👑👑 **ملك الروليت الأسطوري** 👑👑\n\n"
                    f"بكل فخر واعتزاز، نعلن فوز البطل:\n"
                    f"👑 「 {win['name']} 」 👑\n\n"
                    f"بلقب **ملك الروليت** بعد تحقيقه ( 5 ) انتصارات أسطورية!\n"
                    f"🔥🔥 هنيئاً لك هذا العرش يا بطل 🔥🔥\n"
                    f"✨✨✨✨✨✨✨✨✨✨✨✨"
                )
                db.update({'roulette_wins': 0}, User.id == win['id']) # تصفير النقاط بعد التتويج
            else:
                await update.message.reply_text(f"👑👑 مبااااارك الفوز يا اسطورة الروليت 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_wins} )\n👈👈 استمر معنا حتى الجائزة الكبرى 👉👉")
        context.chat_data['r_on'] = False
        return

    # --- 🎲 4. الأوامر وقائمة الألعاب والتكرار ---
    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **عالم مونوبولي العظيم** 👑", reply_markup=get_main_menu_keyboard())
        return

    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **صح!** {u_name} فزت بـ 50,000 دينار ونقطة.")
        context.chat_data['game_ans'] = None
        return

    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        await update.message.reply_text(f"🎮 **{text}**:\n【 {q['question']} 】")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            await query.message.reply_text(f"🎮 **بدأت {game}**:\n【 {q['question']} 】")
