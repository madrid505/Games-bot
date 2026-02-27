import random, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank
from strings import ROULETTE_MESSAGES, GAME_MESSAGES

QUESTIONS = load_questions()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="run_إسلاميات"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="run_ثقافة عامة")],
        [InlineKeyboardButton("🏎️ سيارات", callback_data="run_سيارات"), InlineKeyboardButton("⚽ أندية", callback_data="run_أندية")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="run_عواصم"), InlineKeyboardButton("🚩 أعلام", callback_data="run_أعلام")],
        [InlineKeyboardButton("🔄 عكس", callback_data="run_عكس"), InlineKeyboardButton("🔡 ترتيب", callback_data="run_ترتيب")],
        [InlineKeyboardButton("🧩 تفكيك", callback_data="run_تفكيك"), InlineKeyboardButton("🧮 رياضيات", callback_data="run_رياضيات")],
        [InlineKeyboardButton("🇬🇧 إنجليزي", callback_data="run_إنجليزي"), InlineKeyboardButton("📝 كلمات", callback_data="run_كلمات")],
        [InlineKeyboardButton("🔍 مختلف", callback_data="run_مختلف")],
        [InlineKeyboardButton("💰 الرصيد الملكي", callback_data="cmd_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="cmd_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # 1. تحديث التفاعل
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)

    # 2. فحص الإجابة
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **إجابة صحيحة يا {u_name}!**\n💰 ربحت 50,000 د.")
        context.chat_data['game_ans'] = None
        return

    # 3. أوامر البنك (مربوط بملف bank_handler)
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # 4. تشغيل الألعاب بالكتابة (عواصم، ترتيب، إلخ)
    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        msg = GAME_MESSAGES["game_start"].format(game_name=text, question=q['question'])
        await update.message.reply_text(msg)
        return

    # 5. ملك التفاعل
    if text == "ملك التفاعل":
        all_u = db.all()
        top_active = sorted(all_u, key=lambda x: x.get('msg_count', 0), reverse=True)[:10]
        msg = GAME_MESSAGES["interaction_top"]
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(top_active):
            msg += f"{emojis[i]} {user.get('name', 'لاعب')} ⮕ {user.get('msg_count', 0)} مشاركة\n"
        await update.message.reply_text(msg)
        return

    # 6. الروليت
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text(ROULETTE_MESSAGES["start"])
        return

    if text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == u_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
            await update.message.reply_text(ROULETTE_MESSAGES["register"].format(u_name=u_name))
        return

    if text == "تم" and context.chat_data.get('r_on') and u_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            w_db = db.get(User.id == win['id'])
            new_wins = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_wins}, User.id == win['id'])
            if new_wins >= 5:
                await update.message.reply_text(ROULETTE_MESSAGES["win_king"].format(win_name=win['name']))
                db.update({'roulette_wins': 0}, User.id == win['id'])
            else:
                await update.message.reply_text(ROULETTE_MESSAGES["win_normal"].format(win_name=win['name'], wins_count=new_wins))
        context.chat_data['r_on'] = False
        return

    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text("👑 **عالم مونوبولي العظيم** 👑", reply_markup=get_main_menu_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            msg = GAME_MESSAGES["game_start"].format(game_name=game, question=q['question'])
            await query.message.reply_text(msg)
    elif query.data == "cmd_balance":
        u = db.get(User.id == query.from_user.id)
        await query.message.reply_text(f"💰 **رصيدك الملكي:** {u['balance']:,} د.")
    elif query.data == "cmd_top":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i}- {u['name']} ({u['balance']:,} د)\n"
        await query.message.reply_text(msg)
