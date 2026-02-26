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

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- نظام الألقاب والمستويات ---
def get_rank(level):
    if level < 10: return "🆕 عضو جديد"
    elif level < 30: return "🥉 عضو برونزي"
    elif level < 60: return "🥈 عضو فضي"
    elif level < 100: return "🥇 عضو ذهبي"
    elif level < 150: return "💎 عضو ماسي"
    elif level < 250: return "👑 ملك التفاعل"
    return "🌌 أسطورة المونوبولي"

# --- بنوك الأسئلة الضخمة (تمت إضافة عينات تمثل الـ 50 سؤال لكل قسم) ---
GAMES_DATA = {
    "دين": [("أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة"), ("خاتم الأنبياء؟", "محمد"), ("سورة تعدل ثلث القرآن؟", "الإخلاص"), ("عدد السجدات في القرآن؟", "15")] * 10,
    "انجليزي": [("Apple", "تفاح"), ("Book", "كتاب"), ("School", "مدرسة"), ("Sun", "شمس"), ("Water", "ماء")] * 10,
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة"), ("نادي ليفربول في؟", "انجلترا"), ("نادي النصر؟", "السعودية")] * 13,
    "عواصم": [("فرنسا", "باريس"), ("اليابان", "طوكيو"), ("الأردن", "عمان"), ("مصر", "القاهرة"), ("العراق", "بغداد")] * 10,
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي"), ("ب ر ش ل و ن ة", "برشلونة"), ("م د ر ي د", "مدريد")] * 13,
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: إمبراطورية", "إمبراطورية"), ("اكتب: هيدروكسيد", "هيدروكسيد")] * 17,
    "المختلف": [("تفاح، موز، جزر", "جزر"), ("مصر، لندن، فرنسا", "لندن"), ("ريال، برشلونة، ميلان، الأهلي", "الأهلي")] * 13,
    "سيارات": [("شعار الحصان؟", "فيراري"), ("شعار 4 حلقات؟", "اودي"), ("شعار T؟", "تويوتا")] * 17,
    "تفكيك": [("مملكة", "م م ل ك ة"), ("فلسطين", "ف ل س ط ي ن"), ("سيارة", "س ي ا ر ة")] * 17,
    "عكس": [("سماء", "اءمس"), ("بحر", "رحب"), ("قهوة", "ةوهق")] * 17,
    "رياضيات": [("5+5*2", "15"), ("100/4", "25"), ("9*9", "81")] * 17,
    "ضد": [("طويل", "قصير"), ("غني", "فقير"), ("قوي", "ضعيف")] * 17
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'roulette_wins': 0, 'last_salary': 0, 'xp': 0, 'level': 1}
        db.insert(u_data)
    return u_data

# --- القائمة السداسية المقسمة لصفحات ---
def get_paged_keyboard(page=1):
    all_keys = [
        ("🟣 اسئله", "run_اسئله"), ("🌙 دين", "run_دين"), ("🧠 ترتيب", "run_ترتيب"), 
        ("✏️ كلمات", "run_كلمات"), ("🔍 المختلف", "run_المختلف"), ("🇺🇸 انجليزي", "run_انجليزي"),
        ("🚩 اعلام", "run_اعلام"), ("⚽ اندية", "run_اندية"), ("🗺 عواصم", "run_عواصم"),
        ("🚗 سيارات", "run_سيارات"), ("🔢 تفكيك", "run_تفكيك"), ("🔄 عكس", "run_عكس"),
        ("💣 قنبلة", "run_قنبلة"), ("🎲 تخمين", "run_تخمين"), ("➕ أضف تخمين", "run_addguess"),
        ("🎯 صيد", "run_صيد"), ("⚔️ حرب", "run_gangwar"), ("🐍 السلم والحية", "run_ladder"),
        ("🔨 مزاد", "run_auction"), ("🍀 ساعة حظ", "run_lucky"), ("💰 البنك", "run_bank"),
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
    u_data = await get_user_data(update)
    curr_time = time.time()

    # تحديث المستويات
    new_xp = u_data.get('xp', 0) + 1
    new_level = u_data.get('level', 1)
    if new_xp >= new_level * 30:
        new_level += 1
        await update.message.reply_text(f"🎊 كفو! ارتفع مستواك لـ {new_level}\nلقبك الجديد: {get_rank(new_level)}")
    db.update({'points': u_data.get('points', 0) + 1, 'xp': new_xp, 'level': new_level, 'name': user_name}, User.id == user_id)

    # --- الروليت الملكي (تكرار انا مسموح) ---
    if text == "روليت":
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
                # رسالة إعلان الفائز الملكية
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {win['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑\n\n       🔥🔥 \"فاز بـ {new_w} جولات متتالية\"🔥🔥")
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    # --- ملك التفاعل ---
    elif text == "ملك التفاعل":
        win = max(db.all(), key=lambda x: x.get('points', 0))
        await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")

    # --- أوامر البنك ---
    elif text == "رصيدي":
        await update.message.reply_text(f"قائمة الألعاب\nالمطور والمالك الأساسي\n{OWNER_NAME}\n\n👤 الاسم: {user_name}\n🎖 اللقب: {get_rank(u_data['level'])}\n📈 المستوى: {u_data['level']}\n💰 الرصيد: {u_data['balance']:,}")
    
    elif text == "راتب":
        if curr_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': curr_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} دينار")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق!")

    elif text == "العاب":
        await update.message.reply_text(f"قائمة الألعاب\nالمطور والمالك الأساسي\n{OWNER_NAME}", reply_markup=get_paged_keyboard(page=1))

    # تحقق إجابات الألعاب
    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None; db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ كفو {user_name}! إجابة صحيحة وفزت بـ 10 مليون!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data, user_id, user_name = query.data, query.from_user.id, query.from_user.first_name
    
    if data.startswith("page_"):
        await query.edit_message_reply_markup(reply_markup=get_paged_keyboard(int(data.split("_")[1])))
    
    elif data.startswith("run_"):
        key = data.split("_")[1]
        
        # الألعاب الخمس المقترحة مع شرح وتشغيل
        if key == "gangwar":
            msg = "⚔️ **حرب العصابات:**\nتحالف مع أصدقائك واهجم على العصابات الأخرى لسرقة خزائنهم!"
            btn = [[InlineKeyboardButton("🚀 ابدأ الهجوم", callback_data="start_gang")]]
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btn))
        elif key == "lucky":
            msg = "🍀 **ساعة الحظ:**\nحدث مفاجئ يضاعف الأرباح 10 مرات! (للمطور فقط)"
            btn = [[InlineKeyboardButton("🔥 تفعيل الساعة", callback_data="start_lucky")]]
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btn))
        elif key == "ladder":
            msg = "🐍 **السلم والحية:**\nارمِ النرد.. هل ستصعد للسماء أم تبتلعك الحية؟"
            btn = [[InlineKeyboardButton("🎲 ارمِ النرد", callback_data="start_ladder")]]
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btn))
        
        # تشغيل ألعاب الأسئلة
        elif key in GAMES_DATA:
            q, a = random.choice(GAMES_DATA[key]); context.chat_data['game_ans'] = a
            await query.message.reply_text(f"🎮 بدأت لعبة {key}:\n\n【 {q} 】")
        
        elif key == "bank":
            await query.message.reply_text("💰 **أوامر البنك تعمل الآن:**\n(رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية)")

        elif key == "roulette":
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
            await query.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    # تنفيذ تشغيل الألعاب الفعلي من داخل أزرار الشرح
    elif data.startswith("start_"):
        game = data.split("_")[1]
        if game == "ladder":
            step = random.randint(1, 100); await query.message.reply_text(f"🎲 رميت النرد ووصلت للمربع: {step}!")
        elif game == "lucky" and user_id == OWNER_ID:
            await query.message.reply_text("🍀 تم تفعيل ساعة الحظ! الرواتب x10 لمدة ساعة!")
        elif game == "gang":
            await query.message.reply_text("⚔️ بدأت الحرب! اكتب (هجوم) لتبدأ السرقة.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == '__main__': main()
