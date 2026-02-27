import random
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from games.utils import load_questions
from config import OWNER_ID, GROUP_IDS
from handlers.bank_handler import handle_bank

# تحميل الأسئلة والألعاب
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

    # 1. تحديث عداد ملك التفاعل
    current_msgs = u_data.get('msg_count', 0) + 1
    db.update({'msg_count': current_msgs}, User.id == u_id)

    # 2. أوامر ملك التفاعل (عرض القائمة)
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

    # 3. تمرير الرسالة لملف البنك (إصلاح أوامر حظ، استثمار، كنز، إلخ)
    if await handle_bank(update, u_data, text, u_name, u_id):
        return

    # 4. نظام الروليت الملكي
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب 'انا' 🌹🌹")
        return

    if text == "انا" and context.chat_data.get('r_on'):
        await update.message.reply_text(f"📢🔥🌹 لقد تم تسجيلك يا بطل {u_name} 🌹🔥📢")
        if not any(p['id'] == u_id for p in context.chat_data.get('r_players', [])):
            context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
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
                await update.message.reply_text(f"👑👑 مبااااارك الفوز يا اسطورة الروليت 👑👑\n\n👑 \" {win['name']} \" 👑\n🏆 فوزك رقم: ( {new_wins} )")
        context.chat_data['r_on'] = False
        return

    # 5. التحقق من الإجابة إذا كانت هناك لعبة جارية
    correct_ans = context.chat_data.get('game_ans')
    if correct_ans and text == correct_ans:
        db.update({'balance': u_data['balance'] + 50000, 'points': u_data['points'] + 1}, User.id == u_id)
        await update.message.reply_text(f"✅ **إجابة صحيحة!** {u_name}\n💰 ربحت 50,000 دينار ونقطة تفاعل.")
        context.chat_data['game_ans'] = None
        return

    # 6. تشغيل اللعبة عن طريق كتابة اسمها (مثل: إسلاميات، سيارات، إلخ)
    game_key = None
    # نبحث عن الكلمة في مفاتيح الألعاب
    for key in QUESTIONS.keys():
        if text == key:
            game_key = key
            break
    
    if game_key:
        q = random.choice(QUESTIONS[game_key])
        context.chat_data['game_ans'] = q['answer']
        caption = f"🎮 **بدأت لعبة {game_key}**\n\n━━━━━━━━━━━━━\n【 {q['question']} 】\n━━━━━━━━━━━━━"
        if q.get('image') and os.path.exists(q['image']):
            await update.message.reply_photo(photo=open(q['image'], 'rb'), caption=caption)
        else:
            await update.message.reply_text(caption)
        return

    # 7. الأوامر وقائمة الألعاب
    if text in ["قائمة", "الاوامر", "الأوامر"]:
        await update.message.reply_text(f"👑 **عالم مونوبولي العظيم** 👑", reply_markup=get_main_menu_keyboard())
        return

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # التعامل مع أزرار الألعاب
    if query.data.startswith("run_"):
        game = query.data.replace("run_", "")
        if game in QUESTIONS:
            q = random.choice(QUESTIONS[game])
            context.chat_data['game_ans'] = q['answer']
            caption = f"🎮 **بدأت لعبة {game}**\n\n【 {q['question']} 】"
            await query.message.reply_text(caption)
    
    # التعامل مع أزرار الرصيد والتوب في القائمة
    elif query.data == "cmd_balance":
        u = db.get(User.id == query.from_user.id)
        await query.message.reply_text(f"💰 **رصيدك الملكي:** {u['balance']:,} دينار.")
    elif query.data == "cmd_top":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **قائمة الهوامير:**\n"
        for i, user in enumerate(top, 1): msg += f"{i} - {user['name']} ({user['balance']:,} د)\n"
        await query.message.reply_text(msg)
