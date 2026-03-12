import random
import os
import time
import re
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User, update_card_counter
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank

# 🏷️ الإعدادات الأساسية
CONTEST_NAME = "مسابقة قروب مونوبولي"
SEASON_DURATION_DAYS = 30

SEASON_ALBUM = {
    "card1": "🇧🇷 رونالدو", "card2": "🇷🇸 مودريتش", "card3": "🇵🇹 كريستيانو",
    "card4": "🇧🇷 نيمار", "card5": "🇲🇫 زين الدين زيدان", "card6": "🇮🇹 بيرلو",
    "card7": "🇾🇪 محمد صلاح", "card8": "🇩🇿 رياض محرز", "card9": "🇺🇾 سواريز",
    "card10": "🇲🇦 اشرف حكيمي"
}

QUESTIONS = load_questions()

# 🔄 نظام التوقيت والتصفير التلقائي
def check_and_reset_timers():
    now = datetime.now()
    # تصفير الموسم (30 يوم)
    s_file = "season_start.txt"
    if os.path.exists(s_file):
        with open(s_file, "r") as f: start_date = datetime.strptime(f.read().strip(), "%Y-%m-%d")
        if now >= start_date + timedelta(days=SEASON_DURATION_DAYS):
            db.update({'album': [], 'card_counter': 0}, User.id.exists())
            with open(s_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))
    else:
        with open(s_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))

    # تصفير ملوك التفاعل أسبوعياً (7 أيام)
    w_file = "weekly_reset.txt"
    if os.path.exists(w_file):
        with open(w_file, "r") as f: last_r = datetime.strptime(f.read().strip(), "%Y-%m-%d")
        if now >= last_r + timedelta(days=7):
            with open(w_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))
            return True
    else:
        with open(w_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))
    return False

# 🖼️ تحميل بيانات الألعاب
def load_image_quiz():
    data = []
    if os.path.exists('images.txt'):
        with open('images.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    p = line.strip().split('=')
                    data.append({"file_id": p[0], "answer": p[1]})
    return data

def load_contest_images():
    data = []
    if os.path.exists('contest_images.txt'):
        with open('contest_images.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    p = line.strip().split('=')
                    data.append({"file_id": p[0], "answer": p[1], "rarity": p[2] if len(p) > 2 else "عادية"})
    return data

IMAGE_QUIZ = load_image_quiz()
CONTEST_QUIZ = load_contest_images()

def get_main_menu_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🖼️ لعبة الصور", callback_data="run_image_game"), InlineKeyboardButton("🏆 مسابقة الصور", callback_data="run_contest_game")],
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="run_islamic"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="run_general")],
        [InlineKeyboardButton("🏎️ سيارات", callback_data="run_cars"), InlineKeyboardButton("⚽ أندية", callback_data="run_clubs")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="run_countries"), InlineKeyboardButton("🚩 أعلام", callback_data="run_flags")],
        [InlineKeyboardButton("👑 ملوك التفاعل", callback_data="cmd_top_weekly"), InlineKeyboardButton("💰 الرصيد", callback_data="cmd_balance")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("🎯 أضف تخمين", callback_data="admin_add_guess")])
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    if check_and_reset_timers():
        await broadcast_weekly_kings(update, context)

    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)
    admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
    is_admin = u_id == OWNER_ID or u_id in admins

    # 1. تحديث التفاعل (للأعضاء فقط)
    if not is_admin:
        db.update({'weekly_pts': u_data.get('weekly_pts', 0) + 1}, User.id == u_id)

    # 2. أوامر البنك الملكي
    if await handle_bank(update, u_data, text, u_name, u_id): return

    # 3. نظام "أضف تخمين" (بصيغة التحفيز)
    if text == "اضف تخمين" and is_admin:
        await initiate_guess(update, context, u_name)
        return

    active_g = context.bot_data.get(f"guess_ans_{update.effective_chat.id}")
    if active_g and text == str(active_g):
        del context.bot_data[f"guess_ans_{update.effective_chat.id}"]
        prize = 100000
        db.update({'balance': u_data['balance'] + prize, 'weekly_pts': u_data.get('weekly_pts', 0) + 15}, User.id == u_id)
        await update.message.reply_text(f"🎉 **كفووو يا بطل! لقد فزت!** 🎉\n━━━━━━━━━━━━━━\n🎯 الرقم الصحيح كان: **{text}**\n👤 الفائز: {u_name}\n💰 الجائزة: {prize:,} دينار + 15 نقطة تفاعل\n━━━━━━━━━━━━━━")
        return

    # 4. أوامر الإدارة
    if text == "قفل الالعاب" and is_admin:
        context.chat_data['games_locked'] = True
        await update.message.reply_text("🚫 تم قفل الألعاب من قبل الإدارة."); return
    if text == "فتح الالعاب" and is_admin:
        context.chat_data['games_locked'] = False
        await update.message.reply_text("✅ تم فتح الألعاب.. انطلقوا!"); return
    if text == "ملوك التفاعل":
        await send_weekly_dashboard(update, context); return

    # 5. الألبوم
    if text in ["ألبومي", "البومي"]:
        alb = u_data.get('album', [])
        msg = f"📂 **ألبوم {CONTEST_NAME}** 📂\n\n"
        for cid, cname in SEASON_ALBUM.items():
            msg += f"{'✅' if alb.count(cid) > 0 else '❌'} - {cname} (تملك {alb.count(cid)})\n"
        await update.message.reply_text(msg); return

    # 6. تشغيل الألعاب والداشبورد لكل لعبة
    if not context.chat_data.get('games_locked') or is_admin:
        # إجابات الصور
        if context.chat_data.get('img_ans') == text:
            await process_win(update, context, u_data, u_id, u_name, "images"); return
        
        # إجابات النصوص
        if str(context.chat_data.get('game_ans')) == text:
            await process_win(update, context, u_data, u_id, u_name, "general"); return

        # بدء ألعاب الصور
        if text == "صور" and IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**"); return

        # ألعاب المعلومات العامة
        game_map = {"إسلاميات": "islamic", "ثقافة عامة": "general", "سيارات": "cars", "أندية": "clubs", "عواصم": "countries", "أعلام": "flags", "عكس": "reverse", "ترتيب": "order", "تفكيك": "decompose", "رياضيات": "math", "إنجليزي": "english", "كلمات": "words", "مختلف": "misc"}
        if text in game_map:
            q = random.choice(QUESTIONS[game_map[text]])
            context.chat_data.update({'game_ans': q['answer'], 'game_start_time': time.time()})
            await update.message.reply_text(f"🎮 **بدأت {text}**:\n【 {q['question']} 】"); return

    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **قائمة أوامر {CONTEST_NAME}**", reply_markup=get_main_menu_keyboard(is_admin))

# --- الدوال المساعدة والداشبورد ---
async def initiate_guess(update, context, u_name):
    await update.message.delete()
    bot_un = (await context.bot.get_me()).username
    url = f"https://t.me/{bot_un}?start=guess_{update.effective_chat.id}"
    keyboard = [[InlineKeyboardButton("🔐 اضغط لوضع الرقم في الخاص", url=url)]]
    await update.message.reply_text(
        f"🏰 **مملكة مونوبولي - مسابقة التخمين** 🏰\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📥 **يا {u_name}**، تم فتح الخزنة..\n"
        f"اضغط على الزر بالأسفل لوضع الرقم السري بعيداً عن أعين الاعضاء! 🔥\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🗣️ **يا شعب مونوبولي.. استعدوا للتخمين بمجرد وضع الرقم!**", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_win(update, context, u_data, u_id, u_name, g_type):
    money = 50000
    db.update({'balance': u_data['balance'] + money, 'points': u_data.get('points', 0) + 1}, User.id == u_id)
    
    # نقاط التفاعل للفوز
    if u_id not in [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]:
        db.update({'weekly_pts': u_data.get('weekly_pts', 0) + 2}, User.id == u_id)
    
    win_txt = f"✅ **صح يا أسطورة!** {u_name}\n💰 {money:,} دينار + 1 نقطة"
    context.chat_data.update({'last_win_msg': win_txt, 'last_win_type': g_type, 'game_ans': None, 'img_ans': None})
    
    # زر الداشبورد (دفتر النتائج) الخاص باللعبة
    target_callback = "show_top_images" if g_type == "images" else "show_top_general"
    keyboard = [[InlineKeyboardButton("🏆 دفتر النتائج", callback_data=target_callback)]]
    
    await update.message.reply_text(win_txt, reply_markup=InlineKeyboardMarkup(keyboard))
    await distribute_card(update, u_id)

async def distribute_card(update, u_id):
    u = db.get(User.id == u_id)
    count = u.get('card_counter', 0) + 1
    if count >= 5:
        cid = random.choice(list(SEASON_ALBUM.keys()))
        alb = u.get('album', []); alb.append(cid)
        db.update({'album': alb, 'card_counter': 0}, User.id == u_id)
        await update.message.reply_text(f"🌟 **مبروك!** حصلت على بطاقة ملكية: `{SEASON_ALBUM[cid]}` 📂")
    else:
        db.update({'card_counter': count}, User.id == u_id)

async def send_weekly_dashboard(update, context):
    chat_id = update.effective_chat.id
    admins = [a.user.id for a in await context.bot.get_chat_administrators(chat_id)]
    players = [u for u in db.all() if u.get('id') not in admins]
    top = sorted(players, key=lambda x: x.get('weekly_pts', 0), reverse=True)[:5]
    
    msg = "👑 **لوحة ملوك التفاعل الأسبوعية** 👑\n━━━━━━━━━━━━━━\n"
    emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, user in enumerate(top):
        msg += f"{emojis[i]} **{user.get('name')}** ⮕ `{user.get('weekly_pts', 0)}` نقطة\n"
    msg += "━━━━━━━━━━━━━━\n🔥 *استمروا في التفاعل للوصول للقمة!*"
    
    if update.message: await update.message.reply_text(msg)
    else: await update.callback_query.message.reply_text(msg)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; data = query.data; await query.answer()
    
    # معالجة داشبورد الصور والنقاط
    if data.startswith("show_top_"):
        all_u = db.all()
        sort_key = 'image_points' if "images" in data else 'points'
        top_u = sorted(all_u, key=lambda x: x.get(sort_key, 0), reverse=True)[:10]
        msg = f"📊 **متصدري {('الصور' if 'images' in data else 'النقاط')}** 📊\n\n"
        for i, u in enumerate(top_u): msg += f"{i+1}- {u.get('name')} ⮕ {u.get(sort_key)}\n"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_win")]]))
    
    elif data == "back_to_win":
        msg = context.chat_data.get('last_win_msg', "✅")
        target = "show_top_images" if context.chat_data.get('last_win_type') == "images" else "show_top_general"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data=target)]]))
    
    elif data == "cmd_top_weekly": await send_weekly_dashboard(update, context)
    elif data == "admin_add_guess": await initiate_guess(query, context, query.from_user.first_name)
    
    # بدء الألعاب من القائمة
    elif data == "run_image_game":
        if IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**")
    elif data.startswith("run_"):
        game = data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data.update({'game_ans': q['answer'], 'game_start_time': time.time()})
            await query.message.reply_text(f"🎮 **بدأت {game}**:\n【 {q['question']} 】")
