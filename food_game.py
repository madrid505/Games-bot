# food_game.py
# ملف لعبة خمن الأكلة الإمبراطورية المستقل مع الألقاب ودفتر النتائج والتنقل

import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DB_PATH = "food_game_scores.db"

# بنك الصور المعتمد
ARABIC_FOOD_GAME = [
    {"name": "صيادية سمك", "file_id": "AgACAgQAAxkBAAIRZWqJgebeODAKLypD3CfVKxv-w53JAAIkGWsb_sFIUN5zGwcioygXAQADAgADbQADPQQ="},
    {"name": "مشاوي", "file_id": "AgACAgQAAxkBAAIRZ2qJghH8YvJu5ktk_FLgnyaLeCQZAAIlGWsb_sFIUDwTXCWnTHzPAQADAgADbQADPQQ="},
    {"name": "مقلوبة", "file_id": "AgACAgQAAxkBAAIRaWqJginH9vodibGi5rSa-D8Z8zmUAAImGWsb_sFIULfvJm4cjDGCAQADAgADeAADPQQ="},
    {"name": "صاجية", "file_id": "AgACAgQAAxkBAAIRa2qJgj_OEx8X5yAukZnkcgABGUwQfwACJxlrG_7BSFCorSSxbB-xkwEAAwIAA20AAz0E="},
    {"name": "الشيخ مخشي", "file_id": "AgACAgQAAxkBAAIRbWqJgk6bLvIPAsXuRFCilNbC9rP6AAIoGWsb_sFIUMGPdWjdPb9CAQADAgADbQADPQQ="},
    {"name": "كبسة", "file_id": "AgACAgQAAxkBAAIRb2qJgl-2krM7FM5skzRhne82hH0lAAIpGWsb_sFIUBEx5R9csq0rAQADAgADeQADPQQ="},
    {"name": "ملوخية", "file_id": "AgACAgQAAxkBAAIRcWqJgnj4Vfwo1v7w2JdfwrT5clr1AAIqGWsb_sFIUNP-0W8hjXcQAQADAgADeAADPQQ="},
    {"name": "مسخن", "file_id": "AgACAgQAAxkBAAIRc2qJgpC9GMYieT8mfXxDvwofvIA-AAIrGWsb_sFIUOf4BDzF9q1mAQADAgADeAADPQQ="},
    {"name": "مندي", "file_id": "AgACAgQAAxkBAAIRdWqJgqUaFRX4AnP4u1Ah-dst7_sLAAIsGWsb_sFIUNlD7m7kG2mMAQADAgADeAADPQQ="},
    {"name": "منسف", "file_id": "AgACAgQAAxkBAAIRd2qJgre8LvpBXekyiT8zJkhw2LmSAAItGWsb_sFIUOxWeV07RvPSAQADAgADeQADPQQ="},
    {"name": "ورق عنب", "file_id": "AgACAgQAAxkBAAIReWqJgvhe0X4jCLjzc-5qq3e9FbQ6AAIvGWsb_sFIUM8Rxkxg3wqQAQADAgADbQADPQQ="},
    {"name": "قدرة", "file_id": "AgACAgQAAxkBAAIRe2qJgznQ2-IGakn51U1Fe1favz_VAAIwGWsb_sFIUBBtNKH2NSEHAQADAgADbQADPQQ="}
]

ACTIVE_GAMES = {}

def init_game_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_scores (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        correct_count INTEGER DEFAULT 0
                    )''')
    conn.commit()
    conn.close()

init_game_db()

# دالة لتحديد اللقب حسب عدد النقاط
def get_chef_title(score):
    if score >= 20:
        return "👑 إمبراطور الطهاة"
    elif score >= 15:
        return "🎖️ كبير الطهاة"
    elif score >= 10:
        return "🍳 شيف القروب الرئيسي"
    elif score >= 5:
        return "🥘 طباخ محترف"
    else:
        return "🍳 مساعد طباخ"

# توليد نص وأزرار دفتر النتائج مع نظام الصفحات (Pagination)
def generate_scoreboard_page(page=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, correct_count FROM food_scores ORDER BY correct_count DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "📜 **دفتر نتائج الطهاة فارغ حتى الآن!**", None

    per_page = 5  # عدد الطهاة في كل صفحة
    total_pages = (len(rows) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))

    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_rows = rows[start_idx:end_idx]

    text = "📜 **دفتر نتائج مسابقة الطبخ الإمبراطورية** 📜\n\n━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uname, score) in enumerate(current_rows, start=start_idx + 1):
        title = get_chef_title(score)
        text += f"**{idx}. {uname}**\n   ▫️ الإجابات الصحيحة: `{score}`\n   ▫️ اللقب: **{title}**\n\n"
    
    text += f"━━━━━━━━━━━━━━━━━━━━\n📄 الصفحة `{page + 1}` من `{total_pages}`"

    # إنشاء الأزرار (التالس والسابق)
    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"food_page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"food_page_{page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
    return text, reply_markup

# أمر بدء اللعبة بكلمة (خمن)
async def start_food_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    food = random.choice(ARABIC_FOOD_GAME)
    
    ACTIVE_GAMES[chat_id] = food["name"]

    await update.message.reply_photo(
        photo=food["file_id"],
        caption=(
            "🍽️ **معركة خمن الأكلة الكبرى!**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "**ما هو اسم هذا الطبق الشهي؟**\n"
            "**اكتب إجابتك الآن في المجموعة!**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        parse_mode="Markdown"
    )

# أمر عرض دفتر النتائج بكلمة (شيف)
async def show_scoreboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, reply_markup = generate_scoreboard_page(0)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# معالج أزرار التنقل في دفتر النتائج
async def scoreboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data.startswith("food_page_"):
        return
    
    await query.answer()
    page = int(query.data.split("_")[-1])
    text, reply_markup = generate_scoreboard_page(page)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# معالج استقبال الإجابات والتحقق منها
async def handle_food_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in ACTIVE_GAMES:
        return

    user = update.effective_user
    user_id = user.id
    username = user.first_name
    guess_text = update.message.text.strip()
    correct_answer = ACTIVE_GAMES[chat_id]

    # إذا كانت الإجابة صحيحة
    if guess_text == correct_answer:
        del ACTIVE_GAMES[chat_id]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT correct_count FROM food_scores WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("UPDATE food_scores SET correct_count = correct_count + 1 WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("INSERT INTO food_scores (user_id, username, correct_count) VALUES (?, ?, 1)", (user_id, username))
        conn.commit()
        conn.close()

        # إرسال رسالة النجاح
        await update.message.reply_text(
            f"🎉 **الإجابة صحيحة يا {username}!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"**أحسنت انت طباخ ماهر 🧑‍🍳✨**\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )

        # عرض دفتر النتائج تلقائياً بعد الإجابة الصحيحة
        text, reply_markup = generate_scoreboard_page(0)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    # إذا كانت الإجابة خاطئة
    elif len(guess_text) <= 15 and not guess_text.startswith("/"):
        await update.message.reply_text(
            f"❌ **اجابة خاطئة يا {username}**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"**انت لست طباخ 👨‍🍳🚫**\n\n"
            f"**محروم من مشاركتنا في وجبة الغذاء 🍽️**\n\n"
            f"**عليك جلي الاطباق بعد انتهاؤنا من الطعام 🧼🧽**\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
