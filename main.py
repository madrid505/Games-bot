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

# --- بنك البيانات الضخم (أسئلة غزيرة ومتنوعة) ---
GAMES_DATA = {
    "اسئله": [("عاصمة الأردن؟", "عمان"), ("أطول نهر؟", "النيل"), ("أصغر قارة؟", "استراليا"), ("مخترع الهاتف؟", "غراهام بيل"), ("أين يقع سور الصين؟", "الصين"), ("أكبر محيط؟", "الهادي")],
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة"), ("كم عدد الرسل؟", "313"), ("أول من أسلم من الصبيان؟", "علي بن ابي طالب"), ("صاحب الغار؟", "أبو بكر الصديق")],
    "ثقافه": [("أين يقع تمثال الحرية؟", "نيويورك"), ("معدن سائل؟", "الزئبق"), ("أكبر كوكب؟", "المشتري"), ("مؤلف كتاب القانون في الطب؟", "ابن سينا")],
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي"), ("ب ر ش ل و ن ة", "برشلونة"), ("م د ر ي د", "مدريد"), ("أ ر د ن", "أردن")],
    "تفكيك": [("مملكة", "م م ل ك ة"), ("سيارة", "س ي ا ر ة"), ("كمبيوتر", "ك م ب ي و ت ر"), ("مدرسة", "م د ر س ة")],
    "عكس": [("سماء", "اءمس"), ("قهوة", "ةوهق"), ("كتاب", "باتك"), ("مدرسة", "ةسردم")],
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: بروتوكول", "بروتوكول"), ("اكتب: هيدروكسيد", "هيدروكسيد")],
    "اعلام": [("🇯🇴", "الأردن"), ("🇸🇦", "السعودية"), ("🇵🇸", "فلسطين"), ("🇪🇬", "مصر"), ("🇮🇶", "العراق"), ("🇲🇦", "المغرب")],
    "عواصم": [("فرنسا", "باريس"), ("مصر", "القاهرة"), ("العراق", "بغداد"), ("اليابان", "طوكيو"), ("روسيا", "موسكو")],
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة"), ("نادي ليفربول في؟", "انجلترا")],
    "سيارات": [("شعار الحصان؟", "فيراري"), ("شعار الـ 4 حلقات؟", "اودي"), ("شعار الـ T؟", "تويوتا")],
    "المختلف": [("تفاح، موز، بطاطس، فراولة", "بطاطس"), ("مصر، الأردن، فرنسا، العراق", "فرنسا")],
    "ضد": [("طويل", "قصير"), ("غني", "فقير"), ("سريع", "بطيء"), ("قوي", "ضعيف")],
    "عربي": [("جمع كلمة (رجل)", "رجال"), ("مفرد كلمة (أطفال)", "طفل"), ("جمع (بحر)", "بحار")]
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'roulette_wins': 0, 'last_salary': 0}
        db.insert(u_data)
    return u_data

def get_games_keyboard(page=1):
    if page == 1:
        keyboard = [
            [InlineKeyboardButton("🟣 اسئله", callback_data="run_اسئله"), InlineKeyboardButton("🟣 دين", callback_data="run_دين")],
            [InlineKeyboardButton("🟣 ثقافة", callback_data="run_ثقافه"), InlineKeyboardButton("🟣 تخمين", callback_data="run_تخمين")],
            [InlineKeyboardButton("🟣 صيد", callback_data="run_صيد"), InlineKeyboardButton("🟣 قنبلة", callback_data="run_قنبلة")],
            [InlineKeyboardButton("التالي ➡️", callback_data="page_2")]
        ]
    elif page == 2:
        keyboard = [
            [InlineKeyboardButton("🟣 ترتيب", callback_data="run_ترتيب"), InlineKeyboardButton("🟣 عكس", callback_data="run_عكس")],
            [InlineKeyboardButton("🟣 تفكيك", callback_data="run_تفكيك"), InlineKeyboardButton("🟣 كلمات", callback_data="run_كلمات")],
            [InlineKeyboardButton("🟣 اعلام", callback_data="run_اعلام"), InlineKeyboardButton("🟣 عواصم", callback_data="run_عواصم")],
            [InlineKeyboardButton("⬅️ السابق", callback_data="page_1"), InlineKeyboardButton("التالي ➡️", callback_data="page_3")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🟣 اندية", callback_data="run_اندية"), InlineKeyboardButton("🟣 سيارات", callback_data="run_سيارات")],
            [InlineKeyboardButton("🟣 المختلف", callback_data="run_المختلف"), InlineKeyboardButton("🟣 ضد", callback_data="run_ضد")],
            [InlineKeyboardButton("🟣 عربي", callback_data="run_عربي"), InlineKeyboardButton("🟣 مزاد", callback_data="run_مزاد")],
            [InlineKeyboardButton("⬅️ السابق", callback_data="page_2")]
        ]
    return InlineKeyboardMarkup(keyboard)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, user_id, user_name = update.message.text.strip(), update.effective_user.id, update.effective_user.first_name
    cmd = text.split()[0]
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return
    u_data = await get_user_data(update)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- أوامر البنك الكاملة ---
    if cmd == "رصيدي": await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")
    elif cmd == "راتب":
        if time.time() - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': time.time()}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق")
    elif cmd in ["حظ", "كنز", "بخشيش", "زرف", "استثمار", "مضاربة"]:
        amt = random.randint(1000000, 50000000)
        res = amt if random.random() > 0.5 else -amt
        db.update({'balance': max(0, u_data['balance'] + res)}, User.id == user_id)
        await update.message.reply_text(f"💰 نتيجة {cmd}: {res:,} دينار")

    # --- الروليت وملك التفاعل ---
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
                win = random.choice(players)
                w_db = db.get(User.id == win['id'])
                new_w = (w_db.get('roulette_wins', 0) if w_db else 0) + 1
                db.update({'roulette_wins': new_w}, User.id == win['id'])
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
            context.chat_data['r_on'] = False
    elif text == "ملك التفاعل":
        all_u = db.all()
        if all_u:
            win = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")

    # --- عرض القائمة ---
    elif text == "العاب":
        await update.message.reply_text(f"🎮 **قائمة الألعاب** 🎮\n\nالمطور والمالك: {OWNER_NAME}\n\nتصفح الصفحات وابدأ التحدي:", reply_markup=get_games_keyboard(1))

    # التحقق من الإجابات
    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None; db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ صح يا {user_name}! فزت بـ 10 مليون!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data
    if data.startswith("page_"):
        page = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=get_games_keyboard(page))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        if key in GAMES_DATA:
            q, a = random.choice(GAMES_DATA[key])
            context.chat_data['game_ans'] = a
            await query.message.reply_text(f"🎮 بدأت {key}:\n\n【 {q} 】")
        elif key == "تخمين":
            context.chat_data['guess'] = str(random.randint(1, 10))
            await query.message.reply_text("🎲 خمن رقم من 1 لـ 10")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == '__main__': main()
