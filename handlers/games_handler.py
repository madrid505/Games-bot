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
from royal_messages import (
    WEEKLY_KINGS_DASHBOARD, 
    GUESS_WINNER, 
    CARD_WIN, 
    GUESS_INITIATE, 
    ALBUM_DISPLAY,
    BANK_STATUS
)

# 🏷️ الإعدادات الأساسية
CONTEST_NAME ="خمن الصورة"
SEASON_DURATION_DAYS = 30

SEASON_ALBUM = {
    "card1": "🇧🇷 رونالدو", "card2": "🇷🇸 مودريتش", "card3": "🇵🇹 كريستيانو",
    "card4": "🇧🇷 نيمار", "card5": "🇲🇫 زين الدين زيدان", "card6": "🇮🇹 بيرلو",
    "card7": "🇾🇪 محمد صلاح", "card8": "🇩🇿 رياض محرز", "card9": "🇺🇾 سواريز",
    "card10": "🇲🇦 اشرف حكيمي"
}



# 🔄 نظام التوقيت والتصفير التلقائي
def check_and_reset_timers():
    now = datetime.now()
    # تصفير الموسم (30 يوم)
    s_file = "season_start.txt"
    if os.path.exists(s_file):
        with open(s_file, "r") as f: 
            start_date = datetime.strptime(f.read().strip(), "%Y-%m-%d")
        if now >= start_date + timedelta(days=SEASON_DURATION_DAYS):
            db.update({'album': [], 'card_counter': 0}, User.id.exists())
            with open(s_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))
    else:
        with open(s_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))

    # تصفير ملوك التفاعل أسبوعياً (7 أيام)
    w_file = "weekly_reset.txt"
    if os.path.exists(w_file):
        with open(w_file, "r") as f: 
            last_r = datetime.strptime(f.read().strip(), "%Y-%m-%d")
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
    # قائمة الأزرار مرتبة بشكل ملكي وأنيق
    keyboard = [
        [
            InlineKeyboardButton("🏆 مسابقة الصور", callback_data="run_contest_game"), 
            InlineKeyboardButton("🖼️ لعبة الصور", callback_data="run_image_game")
            
        ],
        [
            InlineKeyboardButton("💡 ثقافة عامة", callback_data="run_general"), 
            InlineKeyboardButton("🕋 اسلاميات", callback_data="run_islamic")
        ],
        [
            InlineKeyboardButton("⚽ أندية", callback_data="run_clubs"), 
            InlineKeyboardButton("🏎️ سيارات", callback_data="run_cars")
        ],
        [
            InlineKeyboardButton("🚩 أعلام", callback_data="run_flags"), 
            InlineKeyboardButton("🌍 عواصم", callback_data="run_countries")
        ],
        # الألعاب التي كانت مفقودة في اللوحة السابقة:
        [
            InlineKeyboardButton("🔄 عكس", callback_data="run_reverse"), 
            InlineKeyboardButton("🧩 تفكيك", callback_data="run_decompose")
        ],
        [
            InlineKeyboardButton("🔢 ترتيب", callback_data="run_order"),
            InlineKeyboardButton("➕ رياضيات", callback_data="run_math")
        ],
        [
            InlineKeyboardButton("🔡 إنجليزي", callback_data="run_english"), 
            InlineKeyboardButton("📝 كلمات", callback_data="run_words")
        ],
        [
            InlineKeyboardButton("💰 الرصيد", callback_data="check_balance"), 
            InlineKeyboardButton("👑 ملوك التفاعل", callback_data="leaderboard")
        ]
    ]
    
    # إضافة زر التخمين في سطر منفصل للمشرفين فقط
    if is_admin:
        keyboard.append([InlineKeyboardButton("🎯 أضف تخمين (إداري)", callback_data="admin_guess")])
        
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
    
    # 👑 [تعديل هام] تعريف الصلاحيات في البداية لتجنب خطأ UnboundLocalError
    admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
    is_admin = u_id == OWNER_ID or u_id in admins

    # --- 👑 تسجيل نقاط التفاعل التلقائي (للأعضاء فقط) ---
    if not is_admin:
        new_weekly_pts = u_data.get('weekly_pts', 0) + 1
        db.update({'weekly_pts': new_weekly_pts}, User.id == u_id)
    # -----------------------------------------------

    # 2. أوامر البنك الملكي
    if await handle_bank(update, u_data, text, u_name, u_id): return

    # 3. نظام "أضف تخمين" (مربوط بالرسالة الملكية)
    if text == "اضف تخمين" and is_admin:
        await initiate_guess(update, context, u_name)
        return

    # 3. نظام التخمين ونظام الـ 5 فوزات (إصلاح شامل)
    active_g = context.bot_data.get(f"guess_ans_{update.effective_chat.id}")
    if active_g is not None and str(text) == str(active_g):
        del context.bot_data[f"guess_ans_{update.effective_chat.id}"]
        
        prize = 100000
        current_wins = u_data.get('guess_wins', 0) + 1
        db.update({
            'balance': u_data['balance'] + prize, 
            'weekly_pts': u_data.get('weekly_pts', 0) + 15,
            'guess_wins': current_wins
        }, User.id == u_id)

        # التحقق من لقب "الإمبراطور" عند الفوز الخامس
        if current_wins >= 5:
            db.update({'guess_wins': 0, 'balance': u_data['balance'] + 500000}, User.id == u_id)
            magic_winner = (
                f"👑 **تتويج ملك التخمين الجديد** 👑\n"
                f"━━━━━━━━━━━━━━\n"
                f"ألف مبروك للأسطورة **{u_name}**!\n"
                f"بعد تحقيق 5 انتصارات متتالية، تفتح لك أبواب الخزنة الملكية.\n\n"
                f"🎖️ **اللقب:** إمبراطور التخمين\n"
                f"💰 **جائزة اللقب:** 500,000 دينار إضافية\n"
                f"━━━━━━━━━━━━━━\n"
                f"✨ تم تصفير نتائجك لتبدأ رحلة ملكية جديدة!"
            )
            await update.message.reply_text(magic_winner)
        else:
            win_msg = GUESS_WINNER.format(text=text, u_name=u_name, prize=prize)
            await update.message.reply_text(f"{win_msg}\n\n📊 **التقدم نحو الملك:** `{current_wins}/5` فوزات")
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

    # 5. الألبوم الملكي
    if text in ["ألبومي", "البومي"]:
        alb = u_data.get('album', [])
        cards_status = ""
        for cid, cname in SEASON_ALBUM.items():
            cards_status += f"{'✅' if alb.count(cid) > 0 else '❌'} - {cname} (تملك {alb.count(cid)})\n"
        await update.message.reply_text(ALBUM_DISPLAY.format(cards_status=cards_status))
        return

    # 6. تشغيل الألعاب
    if not context.chat_data.get('games_locked') or is_admin:
        if context.chat_data.get('img_ans') == text:
            await process_win(update, context, u_data, u_id, u_name, "images"); return
        
    # التحقق من إجابة الأسئلة
    if str(context.chat_data.get('game_ans')) == text:
    # جلب نوع اللعبة التي بدأت من الذاكرة (بدل كلمة general الثابتة)
    current_type = context.chat_data.get('current_game_type', "general")
    await process_win(update, context, u_data, u_id, u_name, current_type)
    return
    

        # تشغيل "صور" نصياً (تحديث لحظي)
        if text == "صور":
            IMAGES = load_image_quiz()
            if IMAGES:
                q = random.choice(IMAGES)
                context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
                await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**"); return

            # تحديث خارطة الألعاب الملكية الخاصة بك
            game_map = {
            "اسلاميات": "islamic", "إسلاميات": "islamic", 
            "ثقافة عامة": "general", "سيارات": "cars", 
            "أندية": "clubs", "عواصم": "countries", 
            "أعلام": "flags", "عكس": "reverse", 
            "ترتيب": "order", "تفكيك": "decompose", 
            "رياضيات": "math", "إنجليزي": "english", 
            "كلمات": "words", "مختلف": "misc",
            "جمع": "words", "مفرد": "words", "مفرد وجمع": "words" 
        }
        
        if text in game_map:
            ALL_QS = load_questions() 
            category = game_map[text]
            if category in ALL_QS and ALL_QS[category]:
                q = random.choice(ALL_QS[category])
                # حفظ الإجابة ونوع اللعبة (category) لضمان توزيع النقاط صح
                context.chat_data.update({
                    'game_ans': q['answer'], 
                    'game_start_time': time.time(),
                    'current_game_type': category  # هذا السطر ضروري جداً
                })
                await update.message.reply_text(f"🎮 **بدأت تحدي {text}**:\n【 {q['question']} 】")
            return
                
            

    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **قائمة أوامر {CONTEST_NAME}**", reply_markup=get_main_menu_keyboard(is_admin))


async def initiate_guess(update, context, u_name):
    """تبدأ عملية التخمين مع منع التداخل وحماية الزر للمشرف فقط"""
    chat_id = update.effective_chat.id
    u_id = update.effective_user.id
    
    # 🚫 التحقق من وجود لعبة صور أو أسئلة أو تخمين نشط حالياً
    if context.chat_data.get('img_ans') or context.chat_data.get('game_ans') or context.bot_data.get(f"guess_ans_{chat_id}"):
        await update.message.reply_text("⚠️ **عفواً سيادة المشرف:** لا يمكن بدء مسابقة تخمين جديدة وهناك لعبة قائمة حالياً!")
        return

    try:
        # جلب معلومات البوت
        bot_obj = await context.bot.get_me()
        
        # بناء الرابط مع إضافة ID المشرف لضمان الصلاحية في الخاص لاحقاً
        url = f"https://t.me/{bot_obj.username}?start=guess_{chat_id}_{u_id}"
        
        keyboard = [[InlineKeyboardButton("🔐 اضغط لوضع الرقم في الخاص", url=url)]]
        
        await update.message.reply_text(
            GUESS_INITIATE.format(u_name=u_name), 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        import logging
        logging.error(f"Error in initiate_guess: {e}")




async def process_win(update, context, u_data, u_id, u_name, g_type):
    money = 50000
    new_img_pts = u_data.get('image_points', 0) + (1 if g_type == "images" else 0)
    db.update({'balance': u_data['balance'] + money, 'points': u_data.get('points', 0) + 1, 'image_points': new_img_pts}, User.id == u_id)
    
    if u_id not in [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]:
        db.update({'weekly_pts': u_data.get('weekly_pts', 0) + 2}, User.id == u_id)
    
    win_txt = f"✅ **صح يا أسطورة!** {u_name}\n💰 {money:,} دينار + 1 نقطة"
    context.chat_data.update({'last_win_msg': win_txt, 'last_win_type': g_type, 'game_ans': None, 'img_ans': None})
    
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
        # استخدام رسالة الفوز بالبطاقة من الملف الملكي
        await update.message.reply_text(CARD_WIN.format(card_name=SEASON_ALBUM[cid]))
    else:
        db.update({'card_counter': count}, User.id == u_id)

async def send_weekly_dashboard(update, context):
    chat_id = update.effective_chat.id
    # جلب قائمة المشرفين والمالك
    admins = [a.user.id for a in await context.bot.get_chat_administrators(chat_id)]
    
    # جلب جميع المستخدمين واستبعاد المشرفين والمالك من القائمة
    players = [u for u in db.all() if u.get('id') not in admins and u.get('id') != OWNER_ID]
    
    # ترتيب اللاعبين بناءً على نقاط التفاعل الأسبوعية
    top = sorted(players, key=lambda x: x.get('weekly_pts', 0), reverse=True)[:5]
    
    emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    top_list_text = ""
    for i, user in enumerate(top):
        top_list_text += f"{emojis[i]} **{user.get('name')}** ⮕ `{user.get('weekly_pts', 0):,}` نقطة\n"
    
    final_msg = WEEKLY_KINGS_DASHBOARD.format(top_list=top_list_text)
    
    if update.message: 
        await update.message.reply_text(final_msg)
    else: 
        await update.callback_query.message.reply_text(final_msg)


async def broadcast_weekly_kings(update, context):
    await send_weekly_dashboard(update, context)
    await context.bot.send_message(update.effective_chat.id, "🔄 **انتهى الأسبوع! تم تتويج الملوك وتصفير النقاط لسباق جديد.**")
    db.update({'weekly_pts': 0}, User.id.exists())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; data = query.data; await query.answer()
    
    if data == "cmd_balance":
        u_data = await get_user_data(query)
        # استخدام قالب الرصيد الملكي من الملف
        msg = BANK_STATUS.format(
            u_name=query.from_user.first_name,
            balance=u_data['balance'],
            points=u_data.get('points', 0),
            img_points=u_data.get('image_points', 0),
            weekly_pts=u_data.get('weekly_pts', 0)
        )
        await query.message.reply_text(msg)

    elif data.startswith("show_top_"):
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
    
    elif data == "run_image_game":
        if IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**")
            
    elif data == "run_contest_game":
        if CONTEST_QUIZ:
            q = random.choice(CONTEST_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🏆 **مسابقة الصور الملكية**\n💎 الندرة: {q.get('rarity', 'عادية')}")

    elif data.startswith("run_"):
        game = data.replace("run_", "")
        # تحديث الأسئلة لحظياً للأزرار
        ALL_QS = load_questions()
        if game in ALL_QS and ALL_QS[game]:
            q = random.choice(ALL_QS[game])
            context.chat_data.update({'game_ans': q['answer'], 'game_start_time': time.time()})
            await query.message.reply_text(f"🎮 **بدأت {game}**:\n【 {q['question']} 】")
        
