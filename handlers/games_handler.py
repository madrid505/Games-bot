import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank

QUESTIONS = load_questions()

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # 1. تحديث التفاعل (دائماً)
    db.update({'msg_count': u_data.get('msg_count', 0) + 1}, User.id == u_id)

    # 2. فحص الإجابة (الأولوية القصوى)
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ صح! {u_name} ربحت 50,000 د.")
        context.chat_data['game_ans'] = None
        return

    # 3. فحص أوامر البنك (استثمار، حظ، راتب...)
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # 4. تشغيل اللعبة بالكتابة (عواصم، ترتيب، إلخ)
    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        caption = f"🎮 بدأت {text}\n━━━━━━━━━━━━━\n【 {q['question']} 】"
        await update.message.reply_text(caption)
        return

    # 5. ملك التفاعل والروليت (كما هي بدون تغيير)
    if text == "ملك التفاعل":
        top = sorted(db.all(), key=lambda x: x.get('msg_count', 0), reverse=True)[:10]
        msg = "👑 ملوك التفاعل:\n"
        for i, u in enumerate(top, 1): msg += f"{i}- {u.get('name')} ({u.get('msg_count', 0)})\n"
        await update.message.reply_text(msg)
        return

    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 بدأت الروليت! اكتب 'انا' للاشتراك.")
        return
    # ... باقي كود الروليت و "انا" و "تم" و "الاوامر" ...
