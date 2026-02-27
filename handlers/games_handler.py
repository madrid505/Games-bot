import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from games.utils import load_questions
from strings import GAME_MESSAGES
from db import db, User

QUESTIONS = load_questions()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="game_إسلاميات"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="game_ثقافة عامة")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="game_عواصم"), InlineKeyboardButton("🚩 أعلام", callback_data="game_أعلام")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="menu_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="menu_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_game_logic(update, context, text):
    # تشغيل اللعبة بالنص
    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        await update.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=text, question=q['question']))
        return True
    
    # فحص الإجابة
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        u_id = update.effective_user.id
        u_db = db.get(User.id == u_id)
        db.update({'balance': u_db.get('balance', 0) + 50000}, User.id == u_id)
        await update.message.reply_text(f"✅ إجابة صحيحة! ربحت 50,000 د.")
        context.chat_data['game_ans'] = None
        return True
    return False

async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("game_"):
        game_type = query.data.replace("game_", "")
        if game_type in QUESTIONS:
            q = random.choice(QUESTIONS[game_type])
            context.chat_data['game_ans'] = q['answer']
            await query.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=game_type, question=q['question']))
    elif query.data == "menu_balance":
        u = db.get(User.id == query.from_user.id)
        await query.message.reply_text(f"💰 رصيدك: {u.get('balance', 0):,} د.")
