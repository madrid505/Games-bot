# food_game.py
# ملف لعبة خمن الأكلة للقروب المحدث (مؤقت 15 ثانية، تلميح، سجل الجلايين، وكل الأفكار الطريفة)

import sqlite3
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DB_PATH = "food_game_scores.db"

# بنك الصور المعتمد (الصور القديمة + الصور الجديدة الإضافية)
ARABIC_FOOD_GAME = [
    # الصور القديمة
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
    {"name": "قدرة", "file_id": "AgACAgQAAxkBAAIRe2qJgznQ2-IGakn51U1Fe1favz_VAAIwGWsb_sFIUBBtNKH2NSEHAQADAgADbQADPQQ="},
    
    # الصور الجديدة التي أرسلتها
    {"name": "كنافة", "file_id": "AgACAgQAAxkBAAIRsWqJvlv5IS3wfqWHEQK2CcKIIO7UAAJhGWsb_sFIUJSjTt_GMAtfAQADAgADeAADPQQ="},
    {"name": "معكرونة", "file_id": "AgACAgQAAxkBAAIRs2qJvrR2n92AV42baAUXnvbdNpwoAAJkGWsb_sFIUPRGFAdK99twAQADAgADeAADPQQ="},
    {"name": "اندومي", "file_id": "AgACAgQAAxkBAAIRtWqJvviN9lsVRIwfPaE8hr7GDevvAAJlGWsb_sFIUCwZYeG7MDKDAQADAgADeAADPQQ="},
    {"name": "بيتزا", "file_id": "AgACAgQAAxkBAAIRt2qJv4WWir1u5iCaSsQPxiX836LTAAJmGWsb_sFIUBNFHLqLuvx7AQADAgADeQADPQQ="},
    {"name": "شاورما", "file_id": "AgACAgQAAxkBAAIRuWqJv-aJUawdkp_lDhIMcmtJPft-AAJnGWsb_sFIUMmoyHk5Lhy4AQADAgADeAADPQQ="},
    {"name": "المسكوف", "file_id": "AgACAgQAAxkBAAIRu2qJwFg6NQShoL-1VN2Op1hr2x45AAJoGWsb_sFIUIHP-bTfj2vUAQADAgADeAADPQQ="},
    {"name": "شيشبرك", "file_id": "AgACAgQAAxkBAAIRvWqJwIZWAXHAAurBKqFe3hys_eDCAAJpGWsb_sFIUPHunS_g7SeOAQADAgADeAADPQQ="},
    {"name": "كوسا محشي", "file_id": "AgACAgQAAxkBAAIRv2qJwKVtG_gJZMZpymtieLWUkyvVAAJqGWsb_sFIUKt6oUvHD-lXAQADAgADeQADPQQ="},
    {"name": "مناقيش زعتر", "file_id": "AgACAgQAAxkBAAIRwWqJwR2wtJdmcKoHoRy643ioh4HzAAJrGWsb_sFIUPx6K_ZI-IR8AQADAgADeAADPQQ="},
    {"name": "صفيحة لحمة", "file_id": "AgACAgQAAxkBAAIRw2qJwUftjGelyU0QXf-yHvE00Q6uAAJsGWsb_sFIUGp6T0nkLnosAQADAgADeAADPQQ="},
    {"name": "كبة", "file_id": "AgACAgQAAxkBAAIRxWqJwWw3lS3CuNfZGImB8YJOPcRcAAJtGWsb_sFIUFmn_0RDk8Y_AQADAgADeAADPQQ="},
    {"name": "سمبوسك", "file_id": "AgACAgQAAxkBAAIRx2qJwZtm04nglCl8Vr5TXE-iOnXiAAJuGWsb_sFIUO86LR01Pp1cAQADAgADeQADPQQ="}
]

ACTIVE_GAMES = {}

# الردود المتنوعة والمضحكة للإجابات الخاطئة
WRONG_RESPONSES = [
    "ههههههههههههههه لا ترجع تدخل المطبخ مره ثانية 🚫",
    "هل انت متأكد انك طباخ سيء؟ 🤔",
    "انت مالك ومال الطبخ عبي كرشك واتوكل 🍔",
    "انت مطلوب منك تجلي الصحون لا تفكر تطبخ ابدا 🧼",
    "انت حرقت الطبيخ والعيال بناموا جوعانين 😭🔥",
    "لم ملابسك وروح على بيت أهلك اتعلم تطبخ وتعال 🧳🏠"
]

# الردود المتنوعة للإجابات الصحيحة
CORRECT_RESPONSES = [
    "احسنت الاجابة صحيحة ✨\nووووه ماي قاد انت طباخ ماهر 🧑‍🍳",
    "احسنت الاجابة صحيحة 👍\nبس حاول ما تنسى الملح 🧂",
    "احسنت الاجابة صحيحة 🌟\nلكن الاكل محروق مو لذيذ 🔥",
    "احسنت الاجابة صحيحة 👏\nبس خلاص لا ترجع تطبخ مره ثانيه 🛑",
    "احسنت الاجابة صحيحة 🏆\nاعتمد على الديليفري وانسى سالفة انك تطبخ 🛵",
    "احسنت الاجابة صحيحة 💯\nانت طباخ ماهر للغاية 👑",
    "احسنت الاجابة صحيحة 🎯\nلكن لو تشتري طعام جاهز بكون افضل 🛒"
]

# مخالفات مطبخية عشوائية عند انتهاء الوقت
TIMEOUT_PENALTIES = [
    "🚨 تم ضبطك تسرق بوظة من الفريزر الساعة 3 بالليل! غرامة 5 جلي صحون.",
    "🚨 حاولت تسوي بيض فحرقت البيت كله! تم سحب رخصة الطبخ منك نهائياً.",
    "🚨 دخلت المطبخ وكسرت طقم الطناجر كله! محكوم بالأعمال الشاقة.",
    "🚨 نسيت الغاز شغال وهربت من الشارع! تم طردك من المطبخ بمهانة."
]

def init_game_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # جدول النقاط
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_scores (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        correct_count INTEGER DEFAULT 0
                    )''')
    # جدول سجل الجلي للأخطاء
    cursor.execute('''CREATE TABLE IF NOT EXISTS dish_washing_records (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        dish_count INTEGER DEFAULT 0
                    )''')
    conn.commit()
    conn.close()

init_game_db()

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

# توليد نص وأزرار دفتر النتائج مع نظام الصفحات
def generate_scoreboard_page(page=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, correct_count FROM food_scores ORDER BY correct_count DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "📜 **دفتر نتائج الطهاة فارغ حتى الآن!**", None

    per_page = 5
    total_pages = (len(rows) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))

    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_rows = rows[start_idx:end_idx]

    text = "📜 **دفتر نتائج مسابقة الطبخ للقروب** 📜\n\n━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uname, score) in enumerate(current_rows, start=start_idx + 1):
        title = get_chef_title(score)
        text += f"**{idx}. {uname}**\n   ▫️ الإجابات الصحيحة: `{score}`\n   ▫️ اللقب: **{title}**\n\n━━━━━━━━━━━━━━━━━━━━\n"
    
    text += f"📄 الصفحة `{page + 1}` من `{total_pages}`"

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

# وظيفة عرض شهادة دبلوم الجلايين وسجل الأخطاء
async def show_dish_washing_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, dish_count FROM dish_washing_records ORDER BY dish_count DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        text = (
            "📜 **سجل دبلوم غسيل الصحون** 📜\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ لا توجد أخطاء مسجلة حتى الآن!\n"
            "يبدو أن الجميع طهاة مهرة (أو لم يطبخوا بعد) 🧑‍🍳✨\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = "📜 **شهادة دبلوم غسيل الصحون وعمداء الجلايين** 📜\n\n━━━━━━━━━━━━━━━━━━━━\n"
        for idx, (uname, count) in enumerate(rows, start=1):
            if idx == 1:
                title = "🧼👑 عميد الجلايين في القروب"
            else:
                title = "🍽️ مساعد جلي صحون"
            
            text += f"**{idx}. {uname}**\n   ▫️ عدد العقوبات/الأخطاء: `{count}` صحن\n   ▫️ الرتبة: **{title}**\n\n━━━━━━━━━━━━━━━━━━━━\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# وظيفة التلميح التلقائي بعد 7 ثوانٍ (مع إضافة تلميح الشيف نصرت)
async def send_hint_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    if chat_id in ACTIVE_GAMES:
        correct_name = ACTIVE_GAMES[chat_id]
        hint_msg = (
            "🚨 **مكالمة استغاثة طارئة من الشيف نصرت!** 👨‍🍳\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📞 الشيف يقول: *\"رش الملح من فوق كوعك يا غبي، الأكلة تتكون من `{len(correct_name)}` أحرف وتبدأ بحرف **{correct_name[0]}**!\"*\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        try:
            await context.bot.send_message(chat_id=chat_id, text=hint_msg, parse_mode="Markdown")
        except Exception:
            pass

# وظيفة انتهاء الوقت بعد 15 ثانية (مع تفتيش أمني للثلاجة ومخالفة عشوائية)
async def timeout_game_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    if chat_id in ACTIVE_GAMES:
        correct_name = ACTIVE_GAMES.pop(chat_id)
        random_penalty = random.choice(TIMEOUT_PENALTIES)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "⏰ **انتهى الوقت المحدد (15 ثانية)!**\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔥 **لقد احترقت الطبخة!** الإجابة الصحيحة كانت: **{correct_name}**\n\n"
                    f"🧊 **تفتيش أمني للثلاجة:**\n{random_penalty}\n"
                    "━━━━━━━━━━━━━━━━━━━━"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass

# أمر بدء اللعبة بكلمة (خمن)
async def start_food_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    current_jobs = context.job_queue.get_jobs_by_name(f"food_game_{chat_id}")
    for j in current_jobs:
        j.schedule_removal()

    food = random.choice(ARABIC_FOOD_GAME)
    ACTIVE_GAMES[chat_id] = food["name"]

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 دفتر النتائج", callback_data="food_show_scoreboard")]
    ])

    await update.message.reply_photo(
        photo=food["file_id"],
        caption=(
            "🍽️ **معركة خمن الأكلة للقروب!**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "**ما هو اسم هذا الطبق الشهي؟**\n"
            "⏱️ **أمامكم 15 ثانية فقط للإجابة!**\n"
            "**اكتب إجابتك الآن في القروب!**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    # جدولة التلميح (الشيف نصرت) بعد 7 ثوانٍ
    context.job_queue.run_once(
        send_hint_job,
        7,
        chat_id=chat_id,
        name=f"food_game_{chat_id}"
    )

    # جدولة انتهاء الوقت بعد 15 ثانية
    context.job_queue.run_once(
        timeout_game_job,
        15,
        chat_id=chat_id,
        name=f"food_game_{chat_id}"
    )

# أمر عرض دفتر النتائج بكلمة (شيف)
async def show_scoreboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, reply_markup = generate_scoreboard_page(0)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# معالج أزرار التنقل ودفتر النتائج عبر الـ Callback
async def scoreboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "food_show_scoreboard":
        await query.answer()
        text, reply_markup = generate_scoreboard_page(0)
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    if data.startswith("food_page_"):
        await query.answer()
        page = int(data.split("_")[-1])
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

    # دعم عرض دبلوم الجلايين عند كتابة كلمة (جلايين) أو (سجل الجلي)
    if guess_text in ["جلايين", "سجل الجلي", "شهادة الجلايين"]:
        await show_dish_washing_record(update, context)
        return

    # إذا كانت الإجابة صحيحة
    if guess_text == correct_answer:
        ACTIVE_GAMES.pop(chat_id, None)
        current_jobs = context.job_queue.get_jobs_by_name(f"food_game_{chat_id}")
        for j in current_jobs:
            j.schedule_removal()

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

        random_correct_response = random.choice(CORRECT_RESPONSES)

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 دفتر النتائج", callback_data="food_show_scoreboard")]
        ])

        await update.message.reply_text(
            f"🎉 **الإجابة صحيحة يا {username}!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"**{random_correct_response}**\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # إذا كانت الإجابة خاطئة
    elif len(guess_text) <= 20 and not guess_text.startswith("/"):
        # تسجيل الخطأ في سجل الجلي الخفي
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT dish_count FROM dish_washing_records WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE dish_washing_records SET dish_count = dish_count + 1 WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("INSERT INTO dish_washing_records (user_id, username, dish_count) VALUES (?, ?, 1)", (user_id, username))
        conn.commit()
        conn.close()

        random_wrong_response = random.choice(WRONG_RESPONSES)
        await update.message.reply_text(
            f"❌ **إجابة خاطئة يا {username}**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"**{random_wrong_response}**\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
