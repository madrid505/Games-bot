import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from strings import GAME_MESSAGES

QUESTIONS = load_questions()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="g_إسلاميات"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="g_ثقافة عامة")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="g_عواصم"), InlineKeyboardButton("🚩 أعلام", callback_data="g_أعلام")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="m_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="m_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_game_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    # تشغيل اللعبة بالنص
    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        await update.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=text, question=q['question']))
        return True
    
    # فحص الإجابة
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        u_data = await get_user_data(update)
        db.update({'balance': u_data['balance'] + 50000}, User.id == update.effective_user.id)
        await update.message.reply_text(f"✅ إجابة صحيحة يا {update.effective_user.first_name}! ربحت 50,000 د.")
        context.chat_data['game_ans'] = None
        return True
    return False

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("g_"):
        game = query.data.replace("g_", "")
        q = random.choice(QUESTIONS[game])
        context.chat_data['game_ans'] = q['answer']
        await query.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=game, question=q['question']))
    elif query.data == "m_balance":
        u = db.get(User.id == query.from_user.id)
        await query.message.reply_text(f"💰 رصيدك: {u.get('balance', 0):,} د.")
