import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

# --- الإعدادات والبيانات الأساسية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
OWNER_NAME = "༺۝༒♛ 🅰🇳🇦🇸 ♛༒۝༻" 

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- نظام الرتب والألقاب ---
def get_rank(level):
    if level < 10: return "🆕 عضو جديد"
    elif level < 30: return "🥉 برونزي"
    elif level < 60: return "🥈 فضي"
    elif level < 100: return "🥇 ذهبي"
    elif level < 150: return "💎 ماسي"
    elif level < 250: return "👑 ملك التفاعل"
    return "🌌 أسطورة المونوبولي"

# --- بنك الأسئلة الضخم (تم تكرارها لضمان الوفرة) ---
QUESTIONS = {
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("ما هي أطول سورة؟", "البقرة"), ("من هو خاتم الأنبياء؟", "محمد"), ("كم عدد الرسل؟", "313"), ("ما هي سورة ثلث القرآن؟", "الاخلاص")] * 15,
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فرنسا؟", "باريس"), ("عاصمة اليابان؟", "طوكيو"), ("عاصمة مصر؟", "القاهرة"), ("عاصمة العراق؟", "بغداد")] * 15,
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة"), ("نادي ليفربول في؟", "انجلترا"), ("نادي النصر؟", "السعودية")] * 15,
    "انجليزي": [("Apple", "تفاح"), ("Book", "كتاب"), ("Car", "سيارة"), ("School", "مدرسة"), ("Sun", "شمس")] * 15,
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي"), ("ب ر ش ل و ن ة", "برشلونة"), ("م د ر ي د", "مدريد")] * 15,
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: إمبراطورية", "إمبراطورية"), ("اكتب: هيدروكسيد", "هيدروكسيد")] * 20,
    "المختلف": [("تفاح، موز، جزر", "جزر"), ("مصر، لندن، فرنسا", "لندن"), ("ريال، برشلونة، الأهلي", "الأهلي")] * 15,
    "تفكيك": [("مملكة", "م م ل ك ة"), ("فلسطين", "ف ل س ط ي ن"), ("سيارة", "س ي ا ر ة")] * 20,
    "عكس": [("سماء", "اءمس"), ("بحر", "رحب"), ("قهوة", "ةوهق")] * 20,
    "رياضيات": [("5+5*2", "15"), ("100/4", "25"), ("9*9", "81")] * 20,
    "ضد": [("طويل", "قصير"), ("غني", "فقير"), ("قوي", "ضعيف")] * 20,
    "سيارات": [("شعار الحصان؟", "فيراري"), ("شعار 4 حلقات؟", "اودي"), ("شعار T؟", "تويوتا")] * 20,
    "اعلام": [("🇯🇴", "الاردن"), ("🇸🇦", "السعودية"), ("🇵🇸", "فلسطين"), ("🇪🇬", "مصر")] * 20
}

async def get_user(uid, name):
    u = db.get(User.id == uid)
    if not u:
        u = {'id': uid, 'name': name, 'balance': 10000000000, 'points': 0, 'xp': 0, 'level': 1, 'last_salary': 0, 'roulette_wins': 0}
        db.insert(u)
    return u

# --- دالة تشغيل الألعاب المركزية ---
async def start_game(game_key, update, context):
    if game_key in QUESTIONS:
        q, a = random.choice(QUESTIONS[game_key])
        context.chat_data['game_ans'] = a
        await update.effective_message.reply_text(f"🎮 بدأت لعبة {game_key}:\n\n【 {q} 】")
    elif game_key == "تخمين":
        context.chat_data['game_ans'] = str(random.randint(1, 10))
        await update.effective_message.reply_text("🎲 خمن الرقم من 1 لـ 10")
    elif game_key == "صيد":
        target = str(random.randint(1000, 9999))
        context.chat_data['game_ans'] = target
        await update.effective_message.reply_text(f"🎯 الأسرع يكتب الرقم: `{target}`")

# --- قائمة الألعاب المنسقة (صفحات) ---
def game_menu(page=1):
    keys = [("🟣 اسئله", "run_اسئله"), ("🌙 دين", "run_دين"), ("🧠 ترتيب", "run_ترتيب"), ("✏️ كلمات", "run_كلمات"), 
            ("🔍 المختلف", "run_المختلف"), ("🇺🇸 انجليزي", "run_انجليزي"), ("🚩 اعلام", "run_اعلام"), ("⚽ اندية", "run_اندية"), 
            ("🗺 عواصم", "run_عواصم"), ("🚗 سيارات", "run_سيارات"), ("🔢 تفكيك", "run_تفكيك"), ("🔄 عكس", "run_عكس"),
            ("💣 قنبلة", "run_قنبلة"), ("🎲 تخمين", "run_تخمين"), ("🎯 صيد", "run_صيد"), ("⚔️ حرب", "run_gangwar"), 
            ("🐍 السلم والحية", "run_ladder"), ("🔨 مزاد", "run_auction"), ("🍀 ساعة حظ", "run_lucky"), ("💰 البنك", "run_bank"), ("🎰 الروليت", "run_roulette")]
    btns = []
    start = (page-1)*6
    current = keys[start:start+6]
    for i in range(0, len(current), 2):
        row = [InlineKeyboardButton(current[i][0], callback_data=current[i][1])]
        if i+1 < len(current): row.append(InlineKeyboardButton(current[i+1][0], callback_data=current[i+1][1]))
        btns.append(row)
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{page-1}"))
    if start+6 < len(keys): nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid, name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    u = await get_user(uid, name)
    
    # تحديث المستوى والخبرة
    new_xp = u.get('xp', 0) + 1
    new_lvl = u.get('level', 1)
    if new_xp >= new_lvl * 50:
        new_lvl += 1
        await update.message.reply_text(f"🆙 كفو {name}! وصلت لفل {new_lvl}\nلقبك الجديد: {get_rank(new_lvl)}")
    db.update({'xp': new_xp, 'level': new_lvl, 'points': u.get('points', 0)+1}, User.id == uid)

    # --- تشغيل الألعاب عبر النص ---
    clean_text = text.replace("لعبة ", "")
    if clean_text in QUESTIONS or clean_text in ["تخمين", "صيد"]:
        await start_game(clean_text, update, context)
        return

    # --- الروليت الملكي (تكرار انا مسموح) ---
    if text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], uid
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
    
    elif text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': uid, 'name': name})
        await update.message.reply_text(f"📢🔥🌹 لقد تم تسجيلك يا {name} 🌹🔥📢")
    
    elif text == "تم" and context.chat_data.get('r_on'):
        if uid == context.chat_data.get('r_starter') or uid == OWNER_ID:
            players = context.chat_data.get('r_players', [])
            if players:
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑\n\n       🔥🔥 \"فاز بـ {new_w} جولات متتالية\"🔥🔥")
                    for user in db.all(): db.update({'roulette_wins': 0}, User.id == user['id'])
            context.chat_data['r_on'] = False

    # --- أوامر البنك ---
    elif text == "رصيدي":
        await update.message.reply_text(f"👤 الاسم: {name}\n🎖 اللقب: {get_rank(u['level'])}\n📈 المستوى: {u['level']}\n💰 الرصيد: {u['balance']:,}")
    elif text == "راتب":
        if time.time() - u.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': u['balance']+amt, 'last_salary': time.time()}, User.id == uid)
            await update.message.reply_text(f"💵 نزل راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")
    elif text in ["كنز", "حظ", "بخشيش", "استثمار", "زرف"]:
        amt = random.randint(2000000, 40000000)
        res = amt if (random.random() > 0.4 or text == "كنز") else -amt
        db.update({'balance': max(0, u['balance']+res)}, User.id == uid)
        await update.message.reply_text(f"💰 نتيجة {text}: {res:,} دينار")

    elif text == "ملك التفاعل":
        top = max(db.all(), key=lambda x: x.get('points', 0))
        await update.message.reply_text(f"🔥🔥 ملك التفاعل: {top['name']}\nالنقاط: {top['points']}\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")

    elif text == "العاب":
        await update.message.reply_text(f"قائمة الألعاب - المالك: {OWNER_NAME}", reply_markup=game_menu(1))

    # تحقق الإجابة
    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None
        db.update({'balance': u['balance'] + 10000000}, User.id == uid)
        await update.message.reply_text(f"✅ صح يا {name}! فزت بـ 10 مليون!")

async def call_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data, uid = query.data, query.from_user.id
    if data.startswith("page_"):
        await query.edit_message_reply_markup(reply_markup=game_menu(int(data.split("_")[1])))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        if key in ["gangwar", "ladder", "auction", "lucky"]:
            desc = {"gangwar": "⚔️ حرب العصابات: اهجم واسرق الخزائن!", "ladder": "🐍 السلم والحية: ارمِ النرد وجرب حظك!", "auction": "🔨 المزاد: زايد على الألقاب النادرة!", "lucky": "🍀 ساعة حظ: للمطور لتفعيل المضاعفات!"}
            await query.message.reply_text(desc[key], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 تشغيل الآن", callback_data=f"start_{key}")]]))
        elif key == "bank": await query.message.reply_text("💰 أوامر البنك: رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، هدية")
        elif key == "roulette": 
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], uid
            await query.message.reply_text("🔥🔥 بدأت الروليت! اكتب (انا) للاشتراك 🔥🔥")
        else: await start_game(key, update, context)
    elif data.startswith("start_"):
        await start_game(data.split("_")[1], update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))
    app.add_handler(CallbackQueryHandler(call_back))
    app.run_polling()

if __name__ == '__main__': main()
