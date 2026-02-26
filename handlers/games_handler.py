import random
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import GROUP_IDS

# تحميل الـ 13 لعبة بالكامل بدون أي نقص
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
        [InlineKeyboardButton("💰 رصيدي الملكي", callback_data="cmd_balance"), InlineKeyboardButton("🏆 قائمة الهوامير", callback_data="cmd_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # حماية أولية لضمان عمل البوت في المجموعات المسموحة فقط
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    # --- 📜 القائمة الرئيسية ---
    if text in ["قائمة", "الاوامر", "الأوامر", "/start"]:
        await update.message.reply_text(
            f"👑 **أهلاً بك في ميسك العظيم** 👑\n\n"
            f"يا {user_name}، اختر لعبتك المفضلة من الأسفل واستعرض رصيدك الملكي.\n",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # --- 🎲 التحقق من الإجابة (إذا كان هناك لعبة تعمل) ---
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        # جائزة اللعبة: 50 ألف دينار + نقطة واحدة
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == user_id)
        await update.message.reply_text(f"✅ **كفو يا بطل!**\n\n【 {user_name} 】\n\nإجابتك صحيحة وفزت بـ 50,000 دينار ونقطة ملكية!")
        context.chat_data['game_ans'] = None # إنهاء اللعبة الحالية
        return

    # --- 🎮 تشغيل الألعاب عبر الكلمات المفتاحية ---
    if text in QUESTIONS:
        q_data = random.choice(QUESTIONS[text])
        context.chat_data['game_ans'] = q_data['answer']
        cap = f"🎮 بدأت لعبة {text}:\n\n━━━━━━━━━━━━━\n【 {q_data['question']} 】\n━━━━━━━━━━━━━\n\nأسرع واحد يجاوب هو الفائز!"
        
        if q_data.get('image') and os.path.exists(q_data['image']):
            await update.message.reply_photo(photo=open(q_data['image'], 'rb'), caption=cap)
        else:
            await update.message.reply_text(cap)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # معالجة ضغطات الأزرار من القائمة
    query = update.callback_query
    await query.answer()
    
    u_id = query.from_user.id
    u_name = query.from_user.first_name
    
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            cap = f"🎮 بدأت {game} (عبر القائمة):\n\n━━━━━━━━━━━━━\n【 {q['question']} 】\n━━━━━━━━━━━━━"
            
            if q.get('image') and os.path.exists(q['image']):
                await query.message.reply_photo(photo=open(q['image'], 'rb'), caption=cap)
            else:
                await query.message.reply_text(cap)

    elif query.data == "cmd_balance":
        u = db.get(User.id == u_id)
        await query.message.reply_text(f"💰 **رصيدك الملكي:**\n\n{u['balance']:,} دينار\n🏆 النقاط: {u['points']}")

    elif query.data == "cmd_top":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **قائمة أغنى 10 هوامير في ميسك:**\n\n"
        for i, u in enumerate(top, 1):
            msg += f"{i} - {u['name']} ⮕ ({u['balance']:,} د)\n"
        await query.message.reply_text(msg)
