import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from strings import GAME_MESSAGES

# استيراد الموزعين الآخرين
from handlers.interaction_handler import update_interaction
from handlers.bank_handler import handle_bank
from handlers.roulette_handler import handle_roulette

# تحميل الأسئلة
QUESTIONS = load_questions()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="game_إسلاميات"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="game_ثقافة عامة")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="game_عواصم"), InlineKeyboardButton("🚩 أعلام", callback_data="game_أعلام")],
        [InlineKeyboardButton("🔄 عكس", callback_data="game_عكس"), InlineKeyboardButton("🔡 ترتيب", callback_data="game_ترتيب")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="menu_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="menu_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الموزع الرئيسي لكل الرسائل النصية في البوت"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # ✅ 1. ملك التفاعل (يحدث العداد مع كل رسالة)
    await update_interaction(update, u_id)

    # ✅ 2. الروليت (يفحص أوامر "انا"، "روليت"، "تم")
    if await handle_roulette(update, context, text, u_id, u_name):
        return

    # ✅ 3. البنك (يفحص أوامر "راتب"، "حظ"، "رصيدي" مع تعديلات Anas)
    if await handle_bank(update, context, text, u_name, u_id):
        return

    # ✅ 4. تشغيل الألعاب بالنصوص (عواصم، أعلام، إلخ)
    if text in QUESTIONS:
        q = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q['answer']
        await update.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=text, question=q['question']))
        return

    # ✅ 5. فحص إذا كانت الرسالة هي إجابة للعبة جارية
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        u_data = await get_user_data(update)
        db.update({'balance': u_data['balance'] + 50000}, User.id == u_id)
        await update.message.reply_text(f"✅ كفو يا {u_name}! إجابتك صحيحة وربحت 50,000 د.")
        context.chat_data['game_ans'] = None # إنهاء اللعبة
        return

    # ✅ 6. أوامر القائمة
    if text in ["الاوامر", "قائمة", "الأوامر"]:
        await update.message.reply_text(
            "👑 **مرحباً بك في عالم مونوبولي الملكي**\n\nاختر اللعبة من الأزرار أو اكتب اسمها مباشرة:",
            reply_markup=get_main_menu_keyboard()
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج ضغطات الأزرار (Callback)"""
    query = update.callback_query
    await query.answer()
    u_id = query.from_user.id
    
    if query.data.startswith("game_"):
        game_type = query.data.replace("game_", "")
        if game_type in QUESTIONS:
            q = random.choice(QUESTIONS[game_type])
            context.chat_data['game_ans'] = q['answer']
            await query.message.reply_text(GAME_MESSAGES["game_start"].format(game_name=game_type, question=q['question']))
    
    elif query.data == "menu_balance":
        u = db.get(User.id == u_id)
        await query.message.reply_text(f"💰 رصيدك الحالي: {u.get('balance', 0):,} د.")
