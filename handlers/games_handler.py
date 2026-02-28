import random
import os
import time
import re
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

# 🖼️ ألبوم أساطير كرة القدم (10 بطاقات)
SEASON_ALBUM = {
    "card1": "🇫🇷 زين الدين زيدان",
    "card2": "🇭🇷 لوكا مودريتش",
    "card3": "🇧🇷 رونالدو (الظاهرة)",
    "card4": "🇵🇹 كريستيانو رونالدو",
    "card5": "🇧🇷 نيمار جونيور",
    "card6": "🇲🇦 أشرف حكيمي",
    "card7": "🇺🇾 لويس سواريز",
    "card8": "🇮🇹 أندريا بيرلو",
    "card9": "🇪🇬 محمد صلاح",
    "card10": "🇩🇿 رياض محرز"
}

QUESTIONS = load_questions()

# 🔄 نظام تصفير الموسم التلقائي
def check_and_reset_season():
    season_file = "season_start.txt"
    now = datetime.now()
    if not os.path.exists(season_file):
        with open(season_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))
        return
    with open(season_file, "r") as f: start_date_str = f.read().strip()
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    if now >= start_date + timedelta(days=SEASON_DURATION_DAYS):
        db.update({'album': [], 'card_counter': 0}, User.id.exists())
        with open(season_file, "w") as f: f.write(now.strftime("%Y-%m-%d"))

# 🖼️ تحميل الصور
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

def get_main_menu_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🖼️ لعبة الصور", callback_data="run_image_game"), InlineKeyboardButton("🏆 مسابقة الصور", callback_data="run_contest_game")],
        [InlineKeyboardButton("🕋 إسلاميات", callback_data="run_islamic"), InlineKeyboardButton("💡 ثقافة عامة", callback_data="run_general")],
        [InlineKeyboardButton("🏎️ سيارات", callback_data="run_cars"), InlineKeyboardButton("⚽ أندية", callback_data="run_clubs")],
        [InlineKeyboardButton("🌍 عواصم", callback_data="run_countries"), InlineKeyboardButton("🚩 أعلام", callback_data="run_flags")],
        [InlineKeyboardButton("🔄 عكس", callback_data="run_reverse"), InlineKeyboardButton("🔡 ترتيب", callback_data="run_order")],
        [InlineKeyboardButton("🧩 تفكيك", callback_data="run_decompose"), InlineKeyboardButton("🧮 رياضيات", callback_data="run_math")],
        [InlineKeyboardButton("🇬🇧 إنجليزي", callback_data="run_english"), InlineKeyboardButton("🔍 مختلف", callback_data="run_misc")],
        [InlineKeyboardButton("💰 الرصيد الملكي", callback_data="cmd_balance"), InlineKeyboardButton("🏆 الهوامير", callback_data="cmd_top")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("📢 نشر الاعلان (خاص)", callback_data="admin_publish")])
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message:
        return

    check_and_reset_season()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
    is_admin = u_id == OWNER_ID or u_id in admins

    # 1. ملك التفاعل (تحديث لحظي)
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)
    if current_msgs >= 1000:
        await update.message.reply_text(f"🔥🔥 **ملك التفاعل الجديد** 🔥🔥\n\nالملك : {u_name}\nالمشاركات : {current_msgs}\n\n🏆 مبارك الفوز يا أسطورة!")
        db.update({'msg_count': 0}, User.id == u_id)

    if not update.message.text: return
    text = update.message.text.strip()

    # 🛑 الإدارة
    if text == "قفل الالعاب" and is_admin:
        context.chat_data['games_locked'] = True
        await update.message.reply_text("🚫 **تم قفل الألعاب من قبل الإدارة.**")
        return
    if text == "فتح الالعاب" and is_admin:
        context.chat_data['games_locked'] = False
        await update.message.reply_text("✅ **تم فتح الألعاب.. انطلقوا!**")
        return
    if text == "نشر الاعلان" and is_admin:
        if os.path.exists("announcement.txt"):
            with open("announcement.txt", "r", encoding="utf-8") as f:
                await update.message.reply_text(f.read())
        return

    # 💰 أوامر البنك الملكي
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # حماية القفل
    game_keywords = ["صور", "مسابقة", "روليت", "إسلاميات", "ثقافة عامة", "سيارات", "أندية", "عواصم", "أعلام", "عكس", "ترتيب", "تفكيك", "رياضيات", "إنجليزي", "مختلف"]
    if context.chat_data.get('games_locked') and text in game_keywords and not is_admin:
        await update.message.reply_text("⚠️ **عذراً، الألعاب مقفلة حالياً.**")
        return

    # 👑 منح بطاقة (للمالك فقط)
    if text.startswith("منح بطاقة") and u_id == OWNER_ID and update.message.reply_to_message:
        try:
            c_num = text.split()[-1]
            card_key = f"card{c_num}"
            if card_key in SEASON_ALBUM:
                target_user = update.message.reply_to_message.from_user
                target_data = db.get(User.id == target_user.id)
                new_alb = target_data.get('album', [])
                new_alb.append(card_key)
                db.update({'album': new_alb}, User.id == target_user.id)
                await update.message.reply_text(f"👑 تم منح {target_user.first_name} بطاقة: `{SEASON_ALBUM[card_key]}` هبة ملكية!")
        except: pass
        return

    # 🤝 التبادل والمبايعة (الرد بـ تم القبول)
    if update.message.reply_to_message:
        match_trade = re.search(r"تبادل بطاقة (\d+) ببطاقة (\d+)", text)
        if match_trade:
            c1, c2 = f"card{match_trade.group(1)}", f"card{match_trade.group(2)}"
            if c1 in u_data.get('album', []) and c2 in SEASON_ALBUM:
                context.chat_data[f"deal_{update.message.message_id}"] = {"type":"trade","from":u_id,"to":update.message.reply_to_message.from_user.id,"give":c1,"take":c2}
                await update.message.reply_text(f"🤝 هل تقبل التبادل؟\nيعطيك: `{SEASON_ALBUM[c1]}`\nيأخذ: `{SEASON_ALBUM[c2]}`\nأجب بـ: **تم القبول**")
            return

        match_sell = re.search(r"بيع بطاقة (\d+) بمبلغ (\d+)", text)
        if match_sell:
            c_key, price = f"card{match_sell.group(1)}", int(match_sell.group(2))
            if c_key in u_data.get('album', []) and price > 0:
                context.chat_data[f"deal_{update.message.message_id}"] = {"type":"sell","seller":u_id,"buyer":update.message.reply_to_message.from_user.id,"card":c_key,"price":price}
                await update.message.reply_text(f"💰 عرض بيع بطاقة `{SEASON_ALBUM[c_key]}` بمبلغ {price:,}\nأجب بـ: **تم القبول**")
            return

        if text == "تم القبول":
            deal = context.chat_data.get(f"deal_{update.message.reply_to_message.message_id}")
            if deal and u_id == (deal.get('to') or deal.get('buyer')):
                if deal['type'] == "trade":
                    target_data = db.get(User.id == u_id)
                    if deal['take'] in target_data.get('album', []):
                        u_src_alb, u_trg_alb = db.get(User.id==deal['from']).get('album', []), target_data.get('album', [])
                        u_src_alb.remove(deal['give']); u_src_alb.append(deal['take'])
                        u_trg_alb.remove(deal['take']); u_trg_alb.append(deal['give'])
                        db.update({'album': u_src_alb}, User.id == deal['from'])
                        db.update({'album': u_trg_alb}, User.id == u_id)
                        await update.message.reply_text("✅ تم التبادل بنجاح!")
                elif deal['type'] == "sell":
                    buyer_data = db.get(User.id == u_id)
                    if buyer_data.get('balance',0) >= deal['price']:
                        seller_data = db.get(User.id == deal['seller'])
                        if deal['card'] in seller_data.get('album',[]):
                            s_alb, b_alb = seller_data.get('album',[]), buyer_data.get('album',[])
                            s_alb.remove(deal['card']); b_alb.append(deal['card'])
                            db.update({'album': s_alb, 'balance': seller_data['balance']+deal['price']}, User.id==deal['seller'])
                            db.update({'album': b_alb, 'balance': buyer_data['balance']-deal['price']}, User.id==u_id)
                            await update.message.reply_text("✅ تمت المبايعة بنجاح!")
            return

    # 🎰 الروليت الملكي
    if text == "روليت" and is_admin:
        context.chat_data.update({'r_on': True, 'r_players': [], 'r_starter': u_id})
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹 ليتم تسجيل اشتراكك اكتب 'انا' 🌹")
        return
    if text == "انا" and context.chat_data.get('r_on'):
        if not any(p['id'] == u_id for p in context.chat_data['r_players']):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
            await update.message.reply_text(f"📢🔥🌹 لقد تم تسجيلك يا بطل {u_name} 🌹🔥📢")
        return
    if text == "تم" and context.chat_data.get('r_on') and u_id == context.chat_data['r_starter']:
        players = context.chat_data.get('r_players', [])
        if players:
            win = random.choice(players); w_db = db.get(User.id == win['id'])
            new_wins = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
            db.update({'roulette_wins': new_wins}, User.id == win['id'])
            if new_wins >= 5:
                await update.message.reply_text(f"👑👑 **ملك الروليت الأسطوري** 👑👑\n👑 「 {win['name']} 」 👑\nتوج باللقب بـ 5 انتصارات!")
                db.update({'roulette_wins': 0}, User.id == win['id'])
            else:
                await update.message.reply_text(f"👑 مباااابارك الفوز يا اسطورة الروليت 👑\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_wins} )")
        context.chat_data['r_on'] = False
        return

    # 🏆 توزيع البطاقات
    async def distribute_card(user_data):
        count = user_data.get('card_counter', 0) + 1
        if count >= 5:
            cid = random.choice(list(SEASON_ALBUM.keys()))
            alb = user_data.get('album', [])
            alb.append(cid)
            db.update({'album': alb, 'card_counter': 0}, User.id == u_id)
            await update.message.reply_text(f"🌟 حصلت على بطاقة: `{SEASON_ALBUM[cid]}` 📂")
            if len(set(alb)) == 10:
                db.update({'balance': user_data['balance']+1000000000, 'points': user_data['points']+500}, User.id==u_id)
                await update.message.reply_text("🎉 ختمت الأبطال! حصلت على المليار + 500 نقطة!")
        else:
            db.update({'card_counter': count}, User.id == u_id)
            await update.message.reply_text(f"🎯 صح! باقي لك {5-count} للبطاقة.")

    # 🎮 تشغيل الألعاب
    if text == "صور":
        if IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **{CONTEST_NAME}**")
        return
    if text == "مسابقة":
        if CONTEST_QUIZ:
            q = random.choice(CONTEST_QUIZ)
            context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🏆 **مسابقة الصور**\n💎 الندرة: {q.get('rarity','عادية')}")
        return

    img_ans = context.chat_data.get('img_ans')
    if img_ans and text == img_ans:
        db.update({'image_points': u_data.get('image_points', 0) + 1}, User.id == u_id)
        win_msg = f"✅ صح يا {u_name}!\n📊 نقاطك: {u_data.get('image_points', 0) + 1}"
        context.chat_data.update({'last_win_msg': win_msg, 'last_win_type': "images", 'img_ans': None})
        await update.message.reply_text(win_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data="show_top_images")]]))
        await distribute_card(u_data)
        return

    game_map = {"إسلاميات":"islamic","ثقافة عامة":"general","سيارات":"cars","أندية":"clubs","عواصم":"countries","أعلام":"flags","عكس":"reverse","ترتيب":"order","تفكيك":"decompose","رياضيات":"math","إنجليزي":"english","مختلف":"misc"}
    if text in game_map:
        key = game_map[text]
        if key in QUESTIONS:
            q = random.choice(QUESTIONS[key])
            context.chat_data.update({'game_ans': q['answer']})
            await update.message.reply_text(f"🎮 **بدأت {text}**:\n【 {q['question']} 】")
            return

    if context.chat_data.get('game_ans') and text == str(context.chat_data.get('game_ans')):
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        win_text = f"✅ صح! {u_name}\n💰 50,000 دينار + 1 نقطة"
        context.chat_data.update({'last_win_msg': win_text, 'last_win_type': "general", 'game_ans': None})
        await update.message.reply_text(win_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data="show_top_general")]]))
        await distribute_card(u_data)
        return

    if text in ["ألبومي", "البومي"]:
        album = u_data.get('album', [])
        msg = f"📂 **ألبوم {CONTEST_NAME}** 📂\n\n"
        for cid, cname in SEASON_ALBUM.items():
            msg += f"{'✅' if cid in album else '❌'} - {cname}\n"
        msg += f"\n📊 الإنجاز: {len(set(album))}/10"
        await update.message.reply_text(msg)
        return

    if text in ["قائمة", "الاوامر"]:
        await update.message.reply_text(f"👑 **{CONTEST_NAME}**", reply_markup=get_main_menu_keyboard(is_admin))

# معالج الأزرار يبقى كما هو مع إضافة حماية admin_publish
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; data = query.data; await query.answer()
    u_id = update.effective_user.id
    admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
    is_admin = u_id == OWNER_ID or u_id in admins

    if data == "admin_publish" and is_admin:
        if os.path.exists("announcement.txt"):
            with open("announcement.txt", "r", encoding="utf-8") as f:
                await query.message.reply_text(f.read())
    elif data.startswith("show_top_"):
        all_u = db.all(); sort_key = 'image_points' if "images" in data else 'points'
        top_u = sorted(all_u, key=lambda x: x.get(sort_key, 0), reverse=True)[:10]
        msg = f"📊 **متصدري {('الصور' if 'images' in data else 'النقاط')}** 📊\n\n"
        for i, u in enumerate(top_u): msg += f"{i+1}- {u.get('name')} ⮕ {u.get(sort_key)}\n"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_win")]]))
    elif data == "back_to_win":
        msg = context.chat_data.get('last_win_msg', "✅")
        target = "show_top_images" if context.chat_data.get('last_win_type') == "images" else "show_top_general"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏆 دفتر النتائج", callback_data=target)]]))
    elif data == "run_image_game":
        if IMAGE_QUIZ:
            q = random.choice(IMAGE_QUIZ); context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🎮 **لعبة الصور**")
    elif data == "run_contest_game":
        if CONTEST_QUIZ:
            q = random.choice(CONTEST_QUIZ); context.chat_data.update({'img_ans': q['answer'], 'img_start_time': time.time()})
            await context.bot.send_photo(update.effective_chat.id, q['file_id'], caption=f"🏆 **مسابقة الصور**")
    elif data.startswith("run_"):
        game = data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game]); context.chat_data.update({'game_ans': q['answer']})
            await query.message.reply_text(f"🎮 **بدأت {game}**:\n【 {q['question']} 】")
