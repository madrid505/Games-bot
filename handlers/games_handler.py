import random
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS

# تحميل كل الأسئلة
QUESTIONS = load_questions()

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الحماية: المجموعات المسموح بها فقط
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # جلب بيانات المستخدم (البنك)
    u_data = await get_user_data(update)

    # --- 1. نظام التحقق من الإجابة (لعبة النقاط) ---
    correct_answer = context.chat_data.get('game_ans')
    if correct_answer and text == correct_answer:
        reward = 50000
        new_balance = u_data.get('balance', 0) + reward
        new_points = u_data.get('points', 0) + 1
        db.update({'balance': new_balance, 'points': new_points}, User.id == user_id)
        
        await update.message.reply_text(
            f"✅ كفو يا {user_name}! إجابة صحيحة.\n"
            f"💰 فزت بـ {reward:,} دينار.\n"
            f"🏆 نقاطك الحالية: {new_points}"
        )
        context.chat_data['game_ans'] = None
        return

    # --- 2. أوامر البنك والترفيه (الدمج الجديد) ---

    # رصيدي
    if text == "رصيدي":
        await update.message.reply_text(
            f"🏦 **بنك مونوبولي العظيم** 🏦\n\n"
            f"👤 الاسم: {user_name}\n"
            f"💰 الرصيد: {u_data['balance']:,} دينار\n"
            f"🏆 النقاط: {u_data['points']}\n"
            f"👑 فوز روليت: {u_data.get('roulette_wins', 0)}"
        )

    # توب (أغنى 10)
    elif text == "توب":
        all_users = db.all()
        top_10 = sorted(all_users, key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في المجموعات:**\n\n"
        for i, user in enumerate(top_10, 1):
            msg += f"{i} - {user['name']} 💰 ({user['balance']:,} د)\n"
        await update.message.reply_text(msg)

    # راتب
    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            salary = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + salary, 'last_salary': now}, User.id == user_id)
            await update.message.reply_text(f"💰 مبروك! استلمت راتبك {salary:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ لسه ما نزل الراتب، باقي {rem} دقيقة.")

    # زرف (بالرد)
    elif text == "زرف" and update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if target_id == user_id: return
        t_db = db.get(User.id == target_id)
        if t_db and t_db.get('balance', 0) > 100000:
            if random.random() < 0.25:
                stolen = random.randint(50000, int(t_db['balance'] * 0.05))
                db.update({'balance': t_db['balance'] - stolen}, User.id == target_id)
                db.update({'balance': u_data['balance'] + stolen}, User.id == user_id)
                await update.message.reply_text(f"🥷 ذيب! زرفت {stolen:,} دينار من {t_db['name']}!")
            else:
                penalty = 100000
                db.update({'balance': max(0, u_data['balance'] - penalty)}, User.id == user_id)
                await update.message.reply_text(f"👮 مسكتك الشرطة! دفعت غرامة {penalty:,} دينار.")

    # كنز
    elif text == "كنز":
        if random.random() < 0.08:
            treasure = random.randint(10000000, 50000000)
            db.update({'balance': u_data['balance'] + treasure}, User.id == user_id)
            await update.message.reply_text(f"🏴‍☠️ يا حظك! لقيت كنز قيمته {treasure:,} دينار!")
        else:
            await update.message.reply_text("🏜️ بحثت وتعبت وما لقيت شيء..")

    # استثمار
    elif text == "استثمار":
        if u_data['balance'] < 1000000:
            return await update.message.reply_text("❌ لازم رصيدك يكون مليون للاستثمار.")
        change = random.randint(100000, 800000)
        if random.random() > 0.5:
            db.update({'balance': u_data['balance'] + change}, User.id == user_id)
            await update.message.reply_text(f"📈 استثمار ناجح! ربحت {change:,} دينار.")
        else:
            db.update({'balance': max(0, u_data['balance'] - change)}, User.id == user_id)
            await update.message.reply_text(f"📉 السوق طاح وخسرت {change:,} دينار.")

    # تحويل (بالرد)
    elif text.startswith("تحويل ") and update.message.reply_to_message:
        try:
            amount = int(text.split()[1])
            if amount > 0 and u_data['balance'] >= amount:
                target_id = update.message.reply_to_message.from_user.id
                t_db = db.get(User.id == target_id)
                if t_db:
                    db.update({'balance': u_data['balance'] - amount}, User.id == user_id)
                    db.update({'balance': t_db['balance'] + amount}, User.id == target_id)
                    await update.message.reply_text(f"💸 تم تحويل {amount:,} دينار إلى {update.message.reply_to_message.from_user.first_name}.")
        except: pass

    # هدية (للمالك فقط بالرد)
    elif text.startswith("هدية ") and user_id == OWNER_ID:
        try:
            amount = int(text.split()[1])
            if update.message.reply_to_message:
                target_id = update.message.reply_to_message.from_user.id
                t_db = db.get(User.id == target_id)
                if t_db:
                    db.update({'balance': t_db['balance'] + amount}, User.id == target_id)
                    await update.message.reply_text(f"🎁 المالك عطاك هدية {amount:,} دينار!")
        except: pass

    # --- 3. لعبة الروليت (النسخة الأصلية التي تفضلها) ---
    if text == "روليت":
        # صلاحية الإدارة (المالك أو المشرفين)
        is_admin = False
        if user_id == OWNER_ID:
            is_admin = True
        else:
            chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            if any(admin.user.id == user_id for admin in chat_admins):
                is_admin = True
        
        if is_admin:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
            await update.message.reply_text(
                "🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n"
                "👈 لقد بدأت لعبة الروليت 👉\n\n"
                "🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹"
            )

    elif text == "انا" and context.chat_data.get('r_on'):
        players = context.chat_data.get('r_players', [])
        if not any(p['id'] == user_id for p in players):
            players.append({'id': user_id, 'name': user_name})
            context.chat_data['r_players'] = players

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
            players = context.chat_data.get('r_players')
            if players:
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                
                await update.message.reply_text(
                    f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n"
                    f"          👑 \" {win['name']} \" 👑\n\n"
                    f"🏆 فوزك رقم: ( {new_w} )"
                )
                
                if new_w >= 5:
                    await update.message.reply_text(
                        f"👑👑👑 ملك الروليت 👑👑👑\n\n"
                        f"             👑 \" {win['name']} \" 👑\n\n"
                        f"       🔥🔥 تم تصفير نقاط الجميع 🔥🔥"
                    )
                    for u in db.all():
                        db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    # --- 4. تشغيل الألعاب (دعم الصور والنصوص) ---
    elif text in QUESTIONS:
        q_set = QUESTIONS[text]
        question_data = random.choice(q_set)
        context.chat_data['game_ans'] = question_data['answer']
        
        # دعم الصور إذا وجدت
        image_path = question_data.get('image')
        if image_path and os.path.exists(image_path):
            await update.message.reply_photo(
                photo=open(image_path, 'rb'),
                caption=f"🎮 بدأت {text}:\n\n【 {question_data['question']} 】"
            )
        else:
            await update.message.reply_text(f"🎮 بدأت {text}:\n\n【 {question_data['question']} 】")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("run_"):
        game_name = data.split("_")[1]
        if game_name in QUESTIONS:
            question = random.choice(QUESTIONS[game_name])
            context.chat_data['game_ans'] = question['answer']
            await query.message.reply_text(f"🎮 بدأت {game_name}:\n\n【 {question['question']} 】")
