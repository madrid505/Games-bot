import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions

OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# تحميل كل الأسئلة
QUESTIONS = load_questions()

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS: 
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # --- لعبة الروليت ---
    if text == "روليت" and (user_id == OWNER_ID or update.effective_user.id in context.chat_data.get('admins', [])):
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text(
            "🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹"
        )
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        # الرد يمكن تعديل تكراره لاحقاً
    elif text == "تم" and context.chat_data.get('r_on'):
        starter = context.chat_data.get('r_starter')
        if user_id == starter or user_id == OWNER_ID:
            players = context.chat_data['r_players']
            if players:
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = (w_db.get('roulette_wins',0) if w_db else 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )")
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑\n\n       🔥🔥 \"{new_w} نقاط\"🔥🔥")
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    # --- لعبة النقاط (أسئلة) ---
    elif text in QUESTIONS:
        q_set = QUESTIONS[text]
        question = random.choice(q_set)
        context.chat_data['game_ans'] = question['answer']
        await update.message.reply_text(f"🎮 بدأت {text}:\n\n【 {question['question']} 】")

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
