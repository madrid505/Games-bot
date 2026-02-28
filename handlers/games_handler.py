import random
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User, add_to_album, update_card_counter  # أضفنا تحديث العداد
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank

# تحميل الأسئلة النصية
QUESTIONS = load_questions()

# 🖼️ إعدادات الموسم (صور الألبوم النادرة)
SEASON_ALBUM = {
    "card1": "🏆 أسطورة مونوبولي",
    "card2": "💎 الملياردير الملكي",
    "card3": "🌟 نجم القروب",
    "card4": "🥇 البطل الخارق",
    "card5": "🔥 شعلة التفاعل"
}

# 🖼️ دالة قراءة صور الألعاب من الملف الخارجي
def load_image_quiz():
    quiz_data = []
    if os.path.exists('images.txt'):
        with open('images.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    f_id, ans = line.split('=', 1)
                    quiz_data.append({"file_id": f_id, "answer": ans})
    return quiz_data

IMAGE_QUIZ = load_image_quiz()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🖼️ لعبة الصور", callback_data="run_image_game")],
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

    # التحقق التلقائي من الإدارة
    admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
    is_admin = u_id == OWNER_ID or u_id in admins

    # 🛑 نظام قفل وفتح الألعاب (للمشرفين فقط)
    if text == "قفل الالعاب" and is_admin:
        context.chat_data['games_locked'] = True
        await update.message.reply_text("🚫 **تم قفل الألعاب من قبل الإدارة.**")
        return
    if text == "فتح الالعاب" and is_admin:
        context.chat_data['games_locked'] = False
        await update.message.reply_text("✅ **تم فتح الألعاب.. انطلقوا!**")
        return

    # 1. تحديث المشاركات (ملك التفاعل)
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)

    # 2. فحص أوامر البنك
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # منع اللاعبين من استخدام أوامر الألعاب إذا كانت مقفلة
    if context.chat_data.get('games_locked') and (text in ["صور", "روليت"] or text in game_map or text in QUESTIONS):
        if not is_admin:
            await update.message.reply_text("⚠️ **عذراً، الألعاب مقفلة حالياً من قبل الإدارة.**")
            return

    # 🏆 نظام توزيع بطاقات الألبوم (تراكمي - 5 نقاط)
    async def distribute_card(user_data):
        current_counter = user_data.get('card_counter', 0) + 1
        
        if current_counter >= 5:
            # منح بطاقة عشوائية
            card_id = random.choice(list(SEASON_ALBUM.keys()))
            card_name = SEASON_ALBUM[card_id]
            if add_to_album(u_id, card_id):
                await update.message.reply_text(f"🌟 **مبروك يا بطل!** لقد جمعت 5 نقاط وحصلت على بطاقة ألبوم عشوائية:\n\n`{card_name}`\n\nتأكد منها في ألبومك! 📂")
            else:
                await update.message.reply_text(f"🌟 لقد حصلت على بطاقة `{card_name}` لكنها موجودة في ألبومك مسبقاً! حاول جمع 5 نقاط أخرى لبطاقة جديدة.")
            
            # تصفير العداد بعد المحاولة (سواء البطاقة جديدة أو مكررة)
            update_card_counter(u_id, 0)
        else:
            # رسالة تحفيزية
            update_card_counter(u_id, current_counter)
            needed = 5 - current_counter
            await update.message.reply_text(f"🎯 **إجابة ذهبية!** أنت الآن مؤهل للحصول على بطاقة جديدة في ألبوم مونوبولي.\n✨ استمر! فاضل لك **{needed}** نقاط فقط لتحصل على بطاقتك القادمة. 🔥")

    # 3. فحص إجابة الصور
    img_ans = context.chat_data.get('img_ans')
    if img_ans and text == img_ans:
        start_time = context.chat_data.get('img_start_time', time.time())
        elapsed_time = round(time.time() - start_time, 2)
        new_img_pts = u_data.get('image_points', 0) + 1
        db.update({'image_points': new_img_pts}, User.id == u_id)
        
        win_msg = (
            f"✅ **صح يا 🎖️ عبقري الصور!**\n\n"
            f"👤 اللاعب: {u_name}\n"
            f"⏱️ الوقت: {elapsed_time} ثانية\n"
            f"🏆 الجائزة: نقطة صور واحدة.\n"
            f"📊 مجموع نقاطك في الصور: {new_img_pts}"
        )
        context.chat_data['last_win_msg'] = win_msg
        context.chat_data['last_win_type'] = "images"
        
        keyboard = [[InlineKeyboardButton("🏆 رؤية دفتر النتائج", callback_data="show_top_images")]]
        await update.message.reply_text(win_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        
        # استدعاء نظام النقاط التراكمي للبطاقات
        await distribute_card(u_data)
        
        context.chat_data['img_ans'] = None
        return

    # 4. ملك التفاعل
    if text == "ملك التفاعل":
        all_u = db.all()
        top_active = sorted(all_u, key=lambda x: x.get('msg_count', 0), reverse=True)[:10]
        msg = "👑 **قائمة ملوك التفاعل - TOP 10** 👑\n\n"
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(top_active):
            msg += f"{emojis[i]} {user.get('name', 'لاعب')} ⮕ {user.get('msg_count', 0)} مشاركة\n"
        await update.message.reply_text(msg)
        return

    if current_msgs >= 1000:
        await update.message.reply_text(f"🔥🔥🔥 **ملك التفاعل** 🔥🔥\n\nاسم الملك : {u_name}\nعدد النقاط : {u_data.get('points', 0)}\nعدد المشاركات : {current_msgs}\n\n🔥🔥 مبارك الفوز يا اسطورة القروب 🔥🔥")
        db.update({'msg_count': 0}, User.id == u_id)
        return

    # أمر ألبومي
    if text == "ألبومي" or text == "البومي":
        album = u_data.get('album', [])
        if not album:
            await update.message.reply_text("📭 ألبومك فارغ.. جاوب على الألعاب لجمع البطاقات!")
        else:
            msg = "📂 **ألبوم الصور الملكي الخاص بك:**\n\n"
            for c_id in album:
                msg += f"🔹 {SEASON_ALBUM.get(c_id)}\n"
            msg += f"\n✅ جمعت {len(album)} من {len(SEASON_ALBUM)}"
            await update.message.reply_text(msg)
        return

    # 5. توب صور
    if text == "توب صور":
        all_u = db.all()
        top_img = sorted(all_u, key=lambda x: x.get('image_points', 0), reverse=True)[:10]
        msg = "🖼️ **لوحة شرف عباقرة الصور - TOP 10** 🖼️\n\n"
        for i, user in enumerate(top_img):
            pts = user.get('image_points', 0)
            if pts > 0: msg += f"{i+1} - {user.get('name', 'لاعب')} ⮕ {pts} نقطة\n"
        await update.message.reply_text(msg if "⮕" in msg else "لا يوجد متصدرين في الصور بعد!")
        return

    # 6. نظام الروليت (تكرار 'انا' مسموح)
    if text == "روليت":
        if is_admin:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب 'انا' 🌹🌹")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
        await update.message.reply_text(f"📢🔥🌹 لقد تم تسجيلك يا بطل {u_name} 🌹🔥📢")
        return

    if text == "تم" and context.chat_data.get('r_on') and u_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players)
            w_db = db.get(User.id == win['id'])
            new_wins = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_wins}, User.id == win['id'])
            if new_wins >= 5:
                await update.message.reply_text(f"✨✨✨✨✨✨✨✨✨✨✨✨\n👑👑 **ملك الروليت الأسطوري** 👑👑\n\n👑 「 {win['name']} 」 👑\n\nلقب **ملك الروليت** بـ 5 انتصارات أسطورية!\n✨✨✨✨✨✨✨✨✨✨✨✨")
                db.update({'roulette_wins': 0}, User.id == win['id'])
            else:
                await update.message.reply_text(f"👑👑 مباااابارك الفوز يا اسطورة الروليت 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_wins} )")
        context.chat_data['r_on'] = False
        return

    # 7. تشغيل الألعاب
    if text == "صور":
        if not IMAGE_QUIZ: return
        quiz = random.choice(IMAGE_QUIZ)
        context.chat_data['img_ans'] = quiz['answer']
        context.chat_data['img_start_time'] = time.time()
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=quiz['file_id'], caption="🎮 **لعبة الصور الملكية بدأت!**\n\nماذا تعني هذه الصورة؟")
        return

    game_map = {"إسلاميات": "islamic", "ثقافة عامة": "general", "سيارات": "cars", "أندية": "clubs", "عواصم": "countries", "أعلام": "flags", "عكس": "reverse", "ترتيب": "order", "تفكيك": "decompose", "رياضيات": "math", "إنجليزي": "english", "كلمات": "words", "مختلف": "misc"}
    if text in game_map:
        game_key = game_map[text]
        if game_key in QUESTIONS:
            q = random.choice(QUESTIONS[game_key])
            context.chat_data['game_ans'] = q['answer']
            context.chat_data['game_start_time'] = time.time()
            await update.message.reply_text(f"🎮 **بدأت {text}**:\n【 {q['question']} 】")
            return

    # 8. التحقق من الإجابة النصية
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == str(correct_ans):
        start_time = context.chat_data.get('game_start_time', time.time())
        elapsed_time = round(time.time() - start_time, 2)
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        
        win_text = (
            f"✅ **صح!** {u_name}\n"
            f"⏱️ الوقت : {elapsed_time} ثانية\n"
            f"📖 الجواب : {correct_ans}\n"
            f"💰 الجائزة : 50,000 دينار + 1 نقطة"
        )
        context.chat_data['last_win_msg'] = win_text
        context.chat_data['last_win_type'] = "general"
        
        keyboard = [[InlineKeyboardButton("🏆 رؤية دفتر النتائج", callback_data="show_top_general")]]
        await update.message.reply_text(win_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        # استدعاء نظام النقاط التراكمي للبطاقات (حتى في الأسئلة النصية لزيادة التنوع)
        await distribute_card(u_data)
        
        context.chat_data['game_ans'] = None
        return

    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **عالم مونوبولي العظيم** 👑", reply_markup=get_main_menu_keyboard())
        return

# معالج الأزرار
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("show_top_"):
        all_u = db.all()
        sort_key = 'image_points' if "images" in data else 'points'
        title = "🖼️ متصدري الصور" if "images" in data else "🏆 متصدري النقاط"
        top_u = sorted(all_u, key=lambda x: x.get(sort_key, 0), reverse=True)[:10]
        
        msg = f"📊 **{title} - TOP 10** 📊\n\n"
        for i, user in enumerate(top_u):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🔹"
            msg += f"{medal} {i+1}- {user.get('name', 'لاعب')} ⮕ {user.get(sort_key, 0)}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_win")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "back_to_win":
        original_msg = context.chat_data.get('last_win_msg', "✅ تمت الإجابة بنجاح!")
        win_type = context.chat_data.get('last_win_type', "general")
        callback_val = "show_top_images" if win_type == "images" else "show_top_general"
        
        keyboard = [[InlineKeyboardButton("🏆 رؤية دفتر النتائج", callback_data=callback_val)]]
        await query.edit_message_text(original_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "run_image_game":
        if not IMAGE_QUIZ: return
        quiz = random.choice(IMAGE_QUIZ)
        context.chat_data['img_ans'] = quiz['answer']
        context.chat_data['img_start_time'] = time.time()
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=quiz['file_id'], caption="🎮 **لعبة الصور الملكية**\nماذا تعني هذه الصورة؟")
        return

    if data.startswith("run_"):
        game = data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            context.chat_data['game_start_time'] = time.time()
            await query.message.reply_text(f"🎮 **بدأت {game}**:\n【 {q['question']} 】")
