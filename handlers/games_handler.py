import random
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS

# تحميل كل الأسئلة عند بدء التشغيل
QUESTIONS = load_questions()

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التأكد أن الرسالة من المجموعات المسموح بها فقط
    if update.effective_chat.id not in GROUP_IDS:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # ضمان وجود بيانات المستخدم في قاعدة البيانات
    u_data = await get_user_data(update)

    # --- أولاً: التحقق من الإجابات (إذا كانت هناك لعبة جارية) ---
    correct_answer = context.chat_data.get('game_ans')
    if correct_answer and text == correct_answer:
        # إضافة رصيد ونقاط للفائز
        new_balance = u_data.get('balance', 0) + 50000
        new_points = u_data.get('points', 0) + 1
        
        db.update({'balance': new_balance, 'points': new_points}, User.id == user_id)
        
        await update.message.reply_text(
            f"✅ إجابة صحيحة يا بطل! \n"
            f"👤 الفائز: {user_name}\n"
            f"💰 الجائزة: 50,000 رصيد\n"
            f"🏆 نقاطك الحالية: {new_points}"
        )
        # إنهاء اللعبة الحالية بمسح الإجابة من الذاكرة
        context.chat_data['game_ans'] = None
        return

    # --- ثانياً: لعبة الروليت ---
    if text == "روليت":
        # التحقق من الصلاحيات (المالك أو المشرفين)
        is_admin = False
        if user_id == OWNER_ID:
            is_admin = True
        else:
            admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            if any(admin.user.id == user_id for admin in admins):
                is_admin = True
        
        if is_admin:
            context.chat_data['r_on'] = True
            context.chat_data['r_players'] = []
            context.chat_data['r_starter'] = user_id
            await update.message.reply_text(
                "🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n"
                "👈 لقد بدأت لعبة الروليت 👉\n\n"
                "🌹 ليتم تسجيل اشتراكك في الجولة اكتب **انا** 🌹"
            )

    elif text == "انا" and context.chat_data.get('r_on'):
        players = context.chat_data.get('r_players', [])
        # منع التكرار
        if not any(p['id'] == user_id for p in players):
            players.append({'id': user_id, 'name': user_name})
            context.chat_data['r_players'] = players
            # اختياري: إرسال تأكيد بسيط أو صامت

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
            players = context.chat_data.get('r_players', [])
            if players:
                winner = random.choice(players)
                w_db = db.get(User.id == winner['id'])
                new_wins = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
                db.update({'roulette_wins': new_wins}, User.id == winner['id'])
                
                await update.message.reply_text(
                    f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n"
                    f"          👑 \" {winner['name']} \" 👑\n\n"
                    f"🏆 فوزك رقم: ( {new_wins} )"
                )
                
                if new_wins >= 5:
                    await update.message.reply_text(
                        f"👑👑👑 ملك الروليت 👑👑👑\n\n"
                        f"             👑 \" {winner['name']} \" 👑\n\n"
                        f"       🔥🔥 تم تصفير عداد الجميع 🔥🔥"
                    )
                    # تصفير عداد الفوز للجميع عند ظهور ملك جديد
                    for u in db.all():
                        db.update({'roulette_wins': 0}, User.id == u['id'])
            
            context.chat_data['r_on'] = False

    # --- ثالثاً: تشغيل ألعاب الأسئلة ---
    # إذا كتب المستخدم اسم اللعبة (مثل: سيارات، اسلاميات، الخ)
    elif text in QUESTIONS:
        q_set = QUESTIONS[text]
        question_data = random.choice(q_set)
        context.chat_data['game_ans'] = question_data['answer']
        
        # التحقق إذا كان هناك صورة للسؤال (ميزة الصور)
        image_path = question_data.get('image') 
        
        if image_path and os.path.exists(image_path):
            await update.message.reply_photo(
                photo=open(image_path, 'rb'),
                caption=f"🎮 بدأت لعبة {text}:\n\n【 {question_data['question']} 】"
            )
        else:
            await update.message.reply_text(
                f"🎮 بدأت لعبة {text}:\n\n"
                f"【 {question_data['question']} 】\n\n"
                f"أسرع إجابة تفوز بـ 50,000 رصيد! 🚀"
            )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("run_"):
        game_name = data.split("_")[1]
        if game_name in QUESTIONS:
            question_data = random.choice(QUESTIONS[game_name])
            context.chat_data['game_ans'] = question_data['answer']
            
            await query.message.reply_text(
                f"🎮 بدأت لعبة {game_name}:\n\n"
                f"【 {question_data['question']} 】"
            )
