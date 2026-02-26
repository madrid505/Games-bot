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

# --- بنك الأسئلة (عينة ضخمة قابلة للتكرار لضمان الـ 50 سؤال) ---
GAMES_DATA = {
    "ترتيب": [("ر ا ل د و ن و", "رونالدو"), ("س ي م ي", "ميسي"), ("ب ر ش ل و ن ة", "برشلونة")] * 20,
    "كلمات": [("اكتب: قسطنطينية", "قسطنطينية"), ("اكتب: هيدروكسيد", "هيدروكسيد")] * 25,
    "المختلف": [("تفاح، موز، جزر", "جزر"), ("مصر، لندن، العراق", "لندن")] * 25,
    "انجليزي": [("معنى Apple؟", "تفاح"), ("معنى Book؟", "كتاب")] * 25,
    "دين": [("أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة")] * 25,
    "اندية": [("نادي الملكي؟", "ريال مدريد"), ("نادي كتالونيا؟", "برشلونة")] * 25
}

async def get_user_data(update: Update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    if not u_data:
        balance = 1000000000000 if user_id == OWNER_ID else 10000000000
        u_data = {'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'roulette_wins': 0, 'last_salary': 0}
        db.insert(u_data)
    return u_data

# --- نظام الصفحات الملكي (كل 6 ألعاب بصفحة) ---
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
    u_data = await get_user_data(update)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- [1] نظام الروليت (السماح بتكرار كلمة انا) ---
    if text == "روليت":
        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
    
    elif text == "انا" and context.chat_data.get('r_on'):
        # هنا تم حذف شرط الـ "any" للسماح بالتكرار كما طلبت
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
                if new_w >= 5:
                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {win['name']} \" 👑\n\n       🔥🔥 \"{new_w} نقاط\"🔥🔥")
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    # --- [2] ملك التفاعل ---
    elif text == "ملك التفاعل":
        all_u = db.all()
        if all_u:
            win = max(all_u, key=lambda x: x.get('points', 0))
            await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {win['name']}\n\nعدد النقاط : {win['points']}\n\nID : {win['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")

    # --- [3] أوامر البنك المباشرة ---
    elif text == "رصيدي": await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} دينار")
    elif text == "العاب":
        await update.message.reply_text(f"قائمة الألعاب\nالمطور والمالك الأساسي\n{OWNER_NAME}", reply_markup=get_paged_keyboard(1))

    # تحقق الإجابات
    if context.chat_data.get('game_ans') and text.lower() == context.chat_data['game_ans'].lower():
        context.chat_data['game_ans'] = None; db.update({'balance': u_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"✅ صح! فزت بـ 10 مليون دينار!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data, user_id = query.data, query.from_user.id
    if data.startswith("page_"):
        await query.edit_message_reply_markup(reply_markup=get_paged_keyboard(int(data.split("_")[1])))
    elif data.startswith("run_"):
        key = data.split("_")[1]
        if key == "bank": await query.message.reply_text("💰 **أوامر البنك:**\n(رصيدي، راتب، زرف، كنز، حظ، بخشيش، استثمار، مضاربة، هدية)")
        elif key == "roulette": 
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
            await query.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
        elif key in GAMES_DATA:
            q, a = random.choice(GAMES_DATA[key]); context.chat_data['game_ans'] = a
            await query.message.reply_text(f"🎮 بدأت {key}:\n\n【 {q} 】")
        else: await query.message.reply_text(f"🚀 بدأت لعبة {key} الآن!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == '__main__': main()
