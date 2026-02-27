import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank
from strings import ROULETTE_MESSAGES, GAME_MESSAGES

# تحميل الأسئلة
QUESTIONS = load_questions()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="game_إسلاميات"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="game_ثقافة عامة")],
        [InlineKeyboardButton("🏎️ سيارات", callback_data="game_سيارات"), InlineKeyboardButton("⚽ أندية", callback_data="game_أندية")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="game_عواصم"), InlineKeyboardButton("🚩 أعلام", callback_data="game_أعلام")],
        [InlineKeyboardButton("🔄 عكس", callback_data="game_عكس"), InlineKeyboardButton("🔡 ترتيب", callback_data="game_ترتيب")],
        [InlineKeyboardButton("🧩 تفكيك", callback_data="game_تفكيك"), InlineKeyboardButton("🧮 رياضيات", callback_data="game_رياضيات")],
        [InlineKeyboardButton("🇬🇧 إنجليزي", callback_data="game_إنجليزي"), InlineKeyboardButton("📝 كلمات", callback_data="game_كلمات")],
        [InlineKeyboardButton("🔍 مختلف", callback_data="game_مختلف")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="menu_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="menu_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # ✅ [حل مشكلة ملك التفاعل]: تحديث عداد الرسائل فوراً مع كل رسالة
    current_count = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_count}, User.id == u_id)

    # ✅ [حل مشكلة تكرار انا]: (كما طلبت فهي تعمل وسأبقيها كما هي)
    if text == "انا" and context.chat_data.get('r_on'):
        if 'r_players' not in context.chat_data: context.chat_data['r_players'] = []
        context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
        await update.message.reply_text(ROULETTE_MESSAGES["register"].format(u_name=u_name))
        return

    # فحص الإجابات الصحيحة للألعاب القائمة
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **كفو يا {u_name}!** إجابة صحيحة.\n💰 ربحت 50,000 د.")
        context.chat_data['game_ans'] = None
        return

    # أوامر البنك (زرف، راتب، إلخ)
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # ✅ [حل مشكلة نصوص الألعاب]: تشغيل اللعبة بمجرد كتابة اسمها
    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        await update.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=text, question=q['question']))
        return

    # أوامر القائمة والروليت
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text(ROULETTE_MESSAGES["start"])
        return

    if text in ["الاوامر", "قائمة"]:
        await update.message.reply_text("👑 **عالم مونوبولي الملكي** 👑", reply_markup=get_main_menu_keyboard())

# ✅ [حل مشكلة الأزرار]: الدالة التي تنفذ الأوامر عند ضغط الزر
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await query.message.reply_text(f"💰 **رصيدك الحالي:** {u['balance']:,} د.")
    elif query.data == "menu_top":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير:**\n"
        for i, u in enumerate(top, 1): msg += f"{i}- {u.get('name', 'لاعب')} ({u.get('balance', 0):,} د)\n"
        await query.message.reply_text(msg)
