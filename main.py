import logging
import random
import time
import asyncio
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

# --- الإعدادات الملكية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🇳🇦🇸 ♛༒۝༻" 
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- نظام الألقاب بناءً على المستوى ---
def get_rank(level):
    if level < 5: return "🆕 عضو جديد"
    if level < 15: return "🥉 عضو برونزي"
    if level < 30: return "🥈 عضو فضي"
    if level < 50: return "🥇 عضو ذهبي"
    if level < 80: return "💎 عضو ماسي"
    if level < 120: return "👑 ملك التفاعل"
    return "🌌 أسطورة المونوبولي"

# --- بنك الأسئلة الشامل ---
GAMES_DATA = {
    "اسئله": [("ما عاصمة الأردن؟", "عمان"), ("أطول نهر؟", "النيل")],
    "دين": [("أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة")],
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي")],
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: إمبراطورية", "إمبراطورية")],
    "المختلف": [("تفاح، موز، جزر", "جزر"), ("مصر، لندن، فرنسا", "فرنسا")],
    "انجليزي": [("معنى Apple؟", "تفاح"), ("معنى Book؟", "كتاب")],
    "اعلام": [("🇯🇴", "الأردن"), ("🇸🇦", "السعودية")],
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة")],
    "عواصم": [("فرنسا", "باريس"), ("اليابان", "طوكيو")],
    "سيارات": [("شعار الحصان؟", "فيراري"), ("شعار 4 حلقات؟", "اودي")],
    "تفكيك": [("مملكة", "م م ل ك ة"), ("فلسطين", "ف ل س ط ي ن")],
    "عكس": [("سماء", "اءمس"), ("بحر", "رحب")],
    "رياضيات": [("5+5*2", "15"), ("100/4", "25")],
    "ضد": [("طويل", "قصير"), ("غني", "فقير")]
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {
            'id': user_id, 'name': update.effective_user.first_name, 
            'balance': balance, 'points': 0, 'roulette_wins': 0, 
            'last_salary': 0, 'xp': 0, 'level': 1
        }
        db.insert(u_data)
    return u_data

def get_paged_keyboard(page=1):
    all_keys = [
        ("🟣 اسئله", "run_اسئله"), ("🌙 دين", "run_دين"), ("🧠 ترتيب", "run_ترتيب"), 
        ("✏️ كلمات", "run_كلمات"), ("🔍 المختلف", "run_المختلف"), ("🇺🇸 انجليزي", "run_انجليزي"),
        ("🚩 اعلام", "run_اعلام"), ("⚽ اندية", "run_اندية"), ("🗺 عواصم", "run_عواصم"),
        ("🚗 سيارات", "run_سيارات"), ("🔢 تفكيك", "run_تفكيك"), ("🔄 عكس", "run_عكس"),
        ("💣 قنبلة", "run_قنبلة"), ("🎲 تخمين", "run_تخمين"), ("➕ أضف تخمين", "run_addguess"),
        ("🎯 صيد", "run_صيد"), ("⚔️ حرب", "run_حرب"), ("🐍 السلم والحية", "run_ladder"),
        ("🔨 مزاد", "run_مزاد"), ("🍀 ساعة حظ", "run_lucky"), ("💰 البنك", "run_bank"),
        ("🎰 الروليت", "run_roulette")
    ]
    start = (page - 1) * 6
    end = start + 6
    current_set = all_keys[start:end]
    buttons = []
    for i in range(0, len(current_set), 2):
        row = [InlineKeyboardButton(current_set[i][0], callback_data=current_set[i][1])]
        if i+1 < len(current_set): row.append(InlineKeyboardButton(current_set[i+1][0], callback_data=current_set[i+1][1]))
        buttons.append(row)
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{page-1}"))
    if end < len(all_keys): nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, user_id, user_name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    curr_time = time.time()
    u_data = await get_user_data(update)
    
    # تحديث النقاط والخبرة
    new_xp = u_data.get('xp', 0) + 1
    new_level = u_data.get('level', 1)
    if new_xp >= new_level * 50: # كل 50 رسالة يرتفع مستوى
        new_level += 1
        await update.message.reply_text(f"🎊 مبارك {user_name}! ارتفع مستواك إلى {new_level}\nلقبك الآن: {get_rank(new_level)}")
    
    db.update({'points': u_data.get('points', 0) + 1, 'xp': new_xp, 'level': new_level, 'name': user_name}, User.id == user_id)

    # --- أوامر البنك ---
    if text == "رصيدي":
        rank = get_rank(u_data.get('level', 1))
        await update.message.reply_text(f"👤 الاسم: {user_name}\n🎖 اللقب: {rank}\n📈 المستوى: {u_data.get('level', 1)}\n💰 رصيدك: {u_data['balance']:,} دينار")
    
    elif text == "راتب":
        if curr_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق")

    elif text in ["كنز", "حظ", "بخشيش", "استثمار", "مضاربة", "زرف"]:
        amt = random.randint(1000000, 50000000)
        res = amt if (random.random() > 0.45 or text == "كنز") else -amt
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"💰 نتيجة {text}: {res:,} دينار")

    # --- الروليت (تكرار انا مسموح) ---
    elif text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")
    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
            players = context.chat_data['r_players']
            if players:
                win = random.choice(players); w_db = db.get(User.id == win['id'])
                new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
            context.chat_data['r_on'] = False

    elif text == "ملك التفاعل":
        all_u = db.all()
        if all_u:
            win = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")

    elif text == "العاب":
        await update.message.reply_text(f"قائمة الألعاب\nالمطور والمالك الأساسي\n{OWNER_NAME}", reply_markup=get_paged_keyboard(1))

    # تحقق الإجابة
    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None; db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ صح يا {user_name}! فزت بـ 10 مليون دينار!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data, user_id = query.data, query.from_user.id
    if data.startswith("page_"):
        await query.edit_message_reply_markup(reply_markup=get_paged_keyboard(int(data.split("_")[1])))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        if key == "bank":
            await query.message.reply_text("💰 **أوامر البنك:**\nرصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية")
        elif key == "roulette":
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
            await query.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
        elif key in GAMES_DATA:
            q, a = random.choice(GAMES_DATA[key]); context.chat_data['game_ans'] = a
            await query.message.reply_text(f"🎮 بدأت {key}:\n\n【 {q} 】")
        else: await query.message.reply_text(f"✅ تم تفعيل {key} بنجاح!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == '__main__': main()
