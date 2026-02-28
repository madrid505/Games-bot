import random
import os
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User, add_to_album, update_card_counter
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank

# 🏷️ إعدادات الموسم الأساسية
CONTEST_NAME = "مسابقة قروب مونوبولي"
SEASON_DURATION_DAYS = 30

# 🖼️ بطاقات الموسم (5 بطاقات لختم الألبوم)
SEASON_ALBUM = {
    "card1": "🏆 أسطورة مونوبولي",
    "card2": "💎 الملياردير الملكي",
    "card3": "🌟 نجم القروب",
    "card4": "🥇 البطل الخارق",
    "card5": "🔥 شعلة التفاعل"
}

QUESTIONS = load_questions()

# 🔄 نظام تصفير الموسم التلقائي
def check_and_reset_season():
    # تخزين تاريخ البداية في ملف بسيط أو قاعدة البيانات
    season_file = "season_start.txt"
    now = datetime.now()
    
    if not os.path.exists(season_file):
        with open(season_file, "w") as f:
            f.write(now.strftime("%Y-%m-%d"))
        return

    with open(season_file, "r") as f:
        start_date_str = f.read().strip()
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    if now >= start_date + timedelta(days=SEASON_DURATION_DAYS):
        # تصفير الألبومات لجميع المستخدمين في قاعدة البيانات
        db.update({'album': [], 'card_counter': 0}, User.id.exists())
        # تحديث تاريخ الموسم الجديد
        with open(season_file, "w") as f:
            f.write(now.strftime("%Y-%m-%d"))

# دالة قراءة الصور
def load_image_quiz():
    quiz_data = []
    if os.path.exists('images.txt'):
        with open('images.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    parts = line.split('=')
                    quiz_data.append({"file_id": parts[0], "answer": parts[1]})
    return quiz_data

def load_contest_images():
    contest_data = []
    if os.path.exists('contest_images.txt'):
        with open('contest_images.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    parts = line.split('=')
                    f_id = parts[0]
                    ans = parts[1]
                    rarity = parts[2] if len(parts) > 2 else "عادية"
                    contest_data.append({"file_id": f_id, "answer": ans, "rarity": rarity})
    return contest_data

IMAGE_QUIZ = load_image_quiz()
CONTEST_QUIZ = load_contest_images()

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🖼️ لعبة الصور", callback_data="run_image_game"), InlineKeyboardButton("🏆 مسابقة الصور", callback_data="run_contest_game")],
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="run_islamic"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="run_general")],
        [InlineKeyboardButton("🏎️ سيارات", callback_data="run_cars"), InlineKeyboardButton("⚽ أندية", callback_data="run_clubs")],
        [InlineKeyboardButton("🔄 عكس", callback_data="run_reverse"), InlineKeyboardButton("🔡 ترتيب", callback_data="run_order")],
        [InlineKeyboardButton("🧩 تفكيك", callback_data="run_decompose"), InlineKeyboardButton("🧮 رياضيات", callback_data="run_math")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="cmd_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="cmd_top")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    check_and_reset_season() # فحص الموسم تلقائياً عند كل رسالة
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
    is_admin = u_id == OWNER_ID or u_id in admins

    if text == "قفل الالعاب" and is_admin:
        context.chat_data['games_locked'] = True
        await update.message.reply_text("🚫 **تم قفل الألعاب من قبل الإدارة.**")
        return
    if text == "فتح الالعاب" and is_admin:
        context.chat_data['games_locked'] = False
        await update.message.reply_text("✅ **تم فتح الألعاب.. انطلقوا!**")
        return

    # 1. ملك التفاعل
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)

    # 2. أوامر البنك
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    game_list = ["صور", "مسابقة", "روليت", "إسلاميات", "ثقافة عامة", "سيارات", "أندية", "عواصم", "أعلام", "عكس", "ترتيب", "تفكيك", "رياضيات", "إنجليزي", "كلمات", "مختلف"]
    if context.chat_data.get('games_locked') and text in game_list and not is_admin:
        await update.message.reply_text("⚠️ **عذراً، الألعاب مقفلة حالياً من قبل الإدارة.**")
        return

    # 🏆 نظام توزيع البطاقات والجائزة الكبرى
    async def distribute_card(user_data):
        current_counter = user_data.get('card_counter', 0) + 1
        if current_counter >= 5:
            available_cards = list(SEASON_ALBUM.keys())
            user_album = user_data.get('album', [])
            card_id = random.choice(available_cards)
            card_name = SEASON_ALBUM[card_id]
            
            if add_to_album(u_id, card_id):
                new_album = user_data.get('album', []) + [card_id]
                await update.message.reply_text(f"🌟 **مبروك!** حصلت على بطاقة ألبوم جديدة:\n`{card_name}`")
                
                # التحقق من ختم الألبوم (جمع 5 بطاقات مختلفة)
                if len(set(new_album)) == 5:
                    # 💰 الجائزة الكبرى
                    grand_prize = 1000000000
                    new_balance = user_data.get('balance', 0) + grand_prize
                    new_points = user_data.get('points', 0) + 500
                    db.update({'balance': new_balance, 'points': new_points}, User.id == u_id)
                    
                    await update.message.reply_text(
                        f"🎉🎊 **إنجاز أسطوري!!!** 🎊🎉\n\n"
                        f"لقد ختمت ألبوم الموسم بالكامل يا {u_name}!\n\n"
                        f"🎁 **جوائزك الملكية:**\n"
                        f"💰 مليار دينار أضيفت لحسابك.\n"
                        f"🏆 500 نقطة في ملك التفاعل.\n"
                        f"🃏 بطاقة نادرة مجهزة لك للموسم القادم.\n\n"
                        f"أنت الآن ملك هذا الموسم بلا منازع! 👑"
                    )
            else:
                await update.message.reply_text(f"🌟 حصلت على بطاقة مكررة: `{card_name}`! استمر.")
            update_card_counter(u_id, 0)
        else:
            update_card_counter(u_id, current_counter)
            await update.message.reply_text(f"🎯 **إجابة صحيحة!** فاضل لك **{5 - current_counter}** نقاط للبطاقة القادمة. 🔥")

    # 3. أمر ألبومي (لعرض النواقص)
    if text in ["ألبومي", "البومي"]:
        album = u_data.get('album', [])
        unique_cards = set(album)
        msg = f"📂 **ألبوم {CONTEST_NAME}** 📂\n\n"
        for cid, cname in SEASON_ALBUM.items():
            status = "✅" if cid in unique_cards else "❌"
            msg += f"{status} - {cname}\n"
        
        msg += f"\n📊 الإنجاز: {len(unique_cards)}/5\n"
        if len(unique_cards) < 5:
            msg += "💡 اجمع البطاقات الناقصة لربح المليار! 💰"
        await update.message.reply_text(msg)
        return

    # 4. الروليت الملكي
    if text == "روليت" and is_admin:
        context.chat_data.update({'r_on': True, 'r_players': [], 'r_starter': u_id})
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹 ليتم تسجيل اشتراكك اكتب 'انا' 🌹")
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
                await update.message.reply_text(f"✨✨✨✨✨✨✨\n👑👑 **ملك الروليت الأسطوري** 👑👑\n\n👑 「 {win['name']} 」 👑\n\nلقب **ملك الروليت** بـ 5 انتصارات! ✨")
                db.update({'roulette_wins': 0}, User.id == win['id'])
            else:
                await update.message.reply_text(f"👑👑 مباااابارك الفوز يا اسطورة الروليت 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_wins} )")
        context.chat_data['r_on'] = False
        return

    # 5. الألعاب والصور
    if text == "صور":
        if IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time(), 'img_rarity': None})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**\nماذا تعني هذه الصورة؟")
        return

    if text == "مسابقة":
        if CONTEST_QUIZ:
            q = random.choice(CONTEST_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time(), 'img_rarity': q['rarity']})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🏆 **{CONTEST_NAME} - مسابقة نادرة**\n💎 الندرة: {q['rarity']}")
        return

    # إجابة الصور
    img_ans = context.chat_data.get('img_ans')
    if img_ans and text == img_ans:
        start_time = context.chat_data.get('img_start_time', time.time())
        elapsed_time = round(time.time() - start_time, 2)
        new_img_pts = u_data.get('image_points', 0) + 1
        db.update({'image_points': new_img_pts}, User.id == u_id)
        win_msg = f"✅ **صح يا عبقري الصور!**\n👤: {u_name}\n⏱️: {elapsed_time}ث\n📊 نقاطك: {new_img_pts}"
        context.chat_data.update({'last_win_msg': win_msg, 'last_win_type': "images", 'img_ans': None})
        await update.message.reply_text(win_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data="show_top_images")]]))
        await distribute_card(u_data)
        return

    # الألعاب النصية
    game_map = {"إسلاميات": "islamic", "ثقافة عامة": "general", "سيارات": "cars", "أندية": "clubs", "عواصم": "countries", "أعلام": "flags", "عكس": "reverse", "ترتيب": "order", "تفكيك": "decompose", "رياضيات": "math", "إنجليزي": "english", "كلمات": "words", "مختلف": "misc"}
    if text in game_map:
        key = game_map[text]
        if key in QUESTIONS:
            q = random.choice(QUESTIONS[key])
            context.chat_data.update({'game_ans': q['answer'], 'game_start_time': time.time()})
            await update.message.reply_text(f"🎮 **بدأت {text}**:\n【 {q['question']} 】")
            return

    # فحص الإجابة النصية
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == str(correct_ans):
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        win_text = f"✅ **صح!** {u_name}\n💰 50,000 دينار + 1 نقطة"
        context.chat_data.update({'last_win_msg': win_text, 'last_win_type': "general", 'game_ans': None})
        await update.message.reply_text(win_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data="show_top_general")]]))
        await distribute_card(u_data)
        return

    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **{CONTEST_NAME}**", reply_markup=get_main_menu_keyboard())

# 🔘 معالج الأزرار
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("show_top_"):
        all_u = db.all()
        sort_key = 'image_points' if "images" in data else 'points'
        title = "🖼️ متصدري الصور" if "images" in data else "🏆 متصدري النقاط"
        top_u = sorted(all_u, key=lambda x: x.get(sort_key, 0), reverse=True)[:10]
        msg = f"📊 **{title}** 📊\n\n"
        for i, u in enumerate(top_u):
            msg += f"{i+1}- {u.get('name')} ⮕ {u.get(sort_key)}\n"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_win")]]))

    elif data == "back_to_win":
        msg = context.chat_data.get('last_win_msg', "✅")
        target = "show_top_images" if context.chat_data.get('last_win_type') == "images" else "show_top_general"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data=target)]]))

    elif data == "run_image_game":
        if IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time(), 'img_rarity': None})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**")

    elif data == "run_contest_game":
        if CONTEST_QUIZ:
            q = random.choice(CONTEST_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time(), 'img_rarity': q['rarity']})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🏆 **مسابقة الصور الملكية**\n💎 الندرة: {q['rarity']}")

    elif data.startswith("run_"):
        game = data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data.update({'game_ans': q['answer'], 'game_start_time': time.time()})
            await query.message.reply_text(f"🎮 **بدأت {game}**:\n【 {q['question']} 】")
