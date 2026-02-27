import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank

# تحميل الأسئلة
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

    # 1. تحديث ملك التفاعل
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)

    # 2. أوامر ملك التفاعل
    if text == "ملك التفاعل":
        all_u = db.all()
        top_active = sorted(all_u, key=lambda x: x.get('msg_count', 0), reverse=True)[:10]
        msg = "👑 **قائمة ملوك التفاعل - TOP 10** 👑\n\n"
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(top_active):
            msg += f"{emojis[i]} {user.get('name', 'لاعب')} ⮕ {user.get('msg_count', 0)} مشاركة\n"
        await update.message.reply_text(msg)
        return

    # 3. تمرير الرسالة للبنك (بدون أي تعديل على أوامره)
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # 4. تفعيل تشغيل الألعاب بالنص (الحل المطلوب)
    game_map = {
        "إسلاميات": "islamic", "ثقافة عامة": "general", "سيارات": "cars", 
        "أندية": "clubs", "عواصم": "countries", "أعلام": "flags", 
        "عكس": "reverse", "ترتيب": "order", "تفكيك": "decompose", 
        "رياضيات": "math", "إنجليزي": "english", "كلمات": "words", "مختلف": "misc"
    }

    if text in game_map:
        game_key = game_map[text]
        if game_key in QUESTIONS:
            q = random.choice(QUESTIONS[game_key])
            context.chat_data['game_ans'] = q['answer']
            await update.message.reply_text(f"🎮 **بدأت {text}**:\n【 {q['question']} 】")
            return

    # 5. التحقق من الإجابة
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == str(correct_ans):
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **صح!** {u_name} فزت بـ 50,000 دينار.")
        context.chat_data['game_ans'] = None
        return

    # 6. الروليت وبقية الأوامر
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 لقد بدأت لعبة الروليت 🔥🔥\n\nاكتب 'انا' للاشتراك.")
        return

    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **عالم مونوبولي العظيم** 👑", reply_markup=get_main_menu_keyboard())
        return

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("run_"):
        game = data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            await query.message.reply_text(f"🎮 **بدأت اللعبة**:\n【 {q['question']} 】")
