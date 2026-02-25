import logging
import random
import time
import os
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# قاعدة البيانات
db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- مكتبة صور ضخمة (روابط تلجرام مباشرة ومستقرة جداً) ---
IMAGE_QUIZ = [
    {"url": "https://telegra.ph/file/1739773295840.jpg", "answer": "ميسي"},
    {"url": "https://telegra.ph/file/1739773345120.jpg", "answer": "رونالدو"},
    {"url": "https://telegra.ph/file/1739773392340.jpg", "answer": "سبونج بوب"},
    {"url": "https://telegra.ph/file/1739773431560.png", "answer": "واتساب"},
    {"url": "https://telegra.ph/file/1739773480000.jpg", "answer": "لوفي"},
    {"url": "https://telegra.ph/file/1739773520000.png", "answer": "يوتيوب"},
    {"url": "https://i.imgur.com/8K0mP0S.png", "answer": "ابل"},
    {"url": "https://i.imgur.com/X9Xf1bY.png", "answer": "بيتزا"},
    {"url": "https://i.imgur.com/xQfW9pL.png", "answer": "برج ايفل"},
    {"url": "https://i.imgur.com/6U8XkM4.png", "answer": "ناروتو"},
    {"url": "https://i.imgur.com/4zQ7KqM.png", "answer": "بيبسي"},
    {"url": "https://i.imgur.com/w9K8f3z.png", "answer": "توم وجيري"},
    {"url": "https://i.imgur.com/Z4vH9vE.png", "answer": "بيكاتشو"},
    {"url": "https://i.imgur.com/lM8K9vP.png", "answer": "ماكدونالدز"},
    {"url": "https://i.imgur.com/rM8K7vR.png", "answer": "سناب شات"}
]

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user: return False, False, False
    user_id = update.effective_user.id
    is_owner = (user_id == OWNER_ID)
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except: is_admin = False
    return True, is_owner, is_admin

async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        _, is_owner, is_admin = await check_auth(update, context)
        # الحفاظ على الأرصدة الضخمة للمالك والمشرفين
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'wins': 0})
        user_data = db.get(User.id == user_id)
    if 'wins' not in user_data: db.update({'wins': 0}, User.id == user_id)
    return user_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return

    allowed, is_owner, is_admin = await check_auth(update, context)
    user_data = await get_user_data(update, context)
    
    # زيادة نقاط التفاعل العامة مع كل رسالة
    db.update({'points': user_data.get('points', 0) + 1}, User.id == user_id)

    # --- القائمة الموحدة ---
    if text in ["العاب", "ألعاب", "الالعاب"]:
        menu = (
            "🎮 **قائمة ألعاب مونوبولي المصلحة** 🎮\n\n"
            "💰 **قسم البنك:** (رصيدي، راتب، كنز، زرف، حظ)\n"
            "🎲 **قسم التفاعل:** (صورة، روليت، ملك التفاعل)\n"
            "⚙️ **التحكم:** (فتح، قفل)"
        )
        await update.message.reply_text(menu, parse_mode="Markdown")
        return

    # --- أوامر التفعيل ---
    if text in ["فتح", "فتح الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['games_active'] = True
            await update.message.reply_text("✅ تم فتح الألعاب بنجاح! استعدوا.")
        return

    # --- رصيدي ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال\n⭐ نقاط تفاعلك: {user_data.get('points', 0)}")

    # --- ملك التفاعل (الرسالة الملكية) ---
    elif text == "ملك التفاعل" and (is_owner or is_admin):
        all_u = db.all()
        if all_u:
            winner = max(all_u, key=lambda x: x.get('points', 0))
            msg = (
                "🔥🔥🔥 ملك التفاعل 🔥🔥\n\n"
                f"اسم الملك : {winner['name']}\n\n"
                f"عدد النقاط : {winner['points']}\n\n"
                f"ID : {winner['id']}\n\n"
                "🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥"
            )
            await update.message.reply_text(msg)
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    # --- الروليت المطور (تكرار انا + نقاط الفوز) ---
    elif text == "روليت":
        if is_owner or is_admin:
            context.chat_data['r_on'] = True
            context.chat_data['r_players'] = []
            context.chat_data['r_starter'] = user_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        # إضافة اللاعب للقائمة (مسموح بالتكرار لزيادة الفرص)
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or is_owner:
            players = context.chat_data.get('r_players', [])
            if players:
                winner_raw = random.choice(players)
                w_id = winner_raw['id']
                w_data = db.get(User.id == w_id)
                new_wins = w_data.get('wins', 0) + 1
                db.update({'wins': new_wins}, User.id == w_id)
                
                win_msg = (
                    "👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n"
                    f"          👑 \" {winner_raw['name']} \" 👑\n\n"
                    f"🏆 عدد مرات فوزك في الروليت حتى الآن: ( {new_wins} )\n\n"
                    "👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉"
                )
                await update.message.reply_text(win_msg)
            context.chat_data['r_on'] = False

    # --- لعبة الصور (استقرار كامل) ---
    elif text in ["صورة", "الصورة", "صوره"]:
        if context.chat_data.get('games_active'):
            try:
                item = random.choice(IMAGE_QUIZ)
                context.chat_data['current_ans'] = item['answer']
                await update.message.reply_photo(photo=item['url'], caption="🖼 وش في الصورة؟ أسرع واحد يجاوب يربح 10 مليون!")
            except:
                await update.message.reply_text("⚠️ زحمة روابط.. حاول تطلب صورة ثانية.")
        else: await update.message.reply_text("🚫 الألعاب مقفلة حالياً.")

    elif context.chat_data.get('current_ans') and text == context.chat_data.get('current_ans'):
        context.chat_data['current_ans'] = None
        db.update({'balance': user_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! إجابة صحيحة وفزت بـ 10,000,000 ريال! ✅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
