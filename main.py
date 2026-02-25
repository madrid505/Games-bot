import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

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
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({
            'id': user_id, 'name': update.effective_user.first_name, 
            'balance': balance, 'points': 0, 'roulette_wins': 0, 
            'stolen_total': 0, 'last_salary': 0, 'last_rob': 0
        })
        user_data = db.get(User.id == user_id)
    if 'roulette_wins' not in user_data: db.update({'roulette_wins': 0}, User.id == user_id)
    return user_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    full_text = update.message.text.strip()
    parts = full_text.split()
    cmd = parts[0]
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return
    allowed, is_owner, is_admin = await check_auth(update, context)
    u_data = await get_user_data(update, context)
    
    # نقاط ملك التفاعل
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- أوامر البنك والتحكم ---
    if full_text in ["فتح", "فتح الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['active'] = True
            await update.message.reply_text("✅ تم فتح الألعاب والبنك!")
        return

    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} ريال")

    elif cmd == "راتب":
        if current_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الراتب كل 10 دقائق")

    elif cmd == "هدية" and len(parts) > 1 and update.message.reply_to_message:
        try:
            gift = int(parts[1])
            target_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= gift > 0:
                db.update({'balance': u_data['balance'] - gift}, User.id == user_id)
                db.update({'balance': db.get(User.id == target_id)['balance'] + gift}, User.id == target_id)
                await update.message.reply_text(f"🎁 تم إرسال {gift:,} ريال كهدية")
        except: pass

    # --- ملك التفاعل (الرسالة الملكية الأصلية) ---
    elif full_text == "ملك التفاعل" and (is_owner or is_admin):
        winner = max(db.all(), key=lambda x: x.get('points', 0))
        msg = (f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {winner['name']}\n\nعدد النقاط : {winner['points']}\n\nID : {winner['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
        await update.message.reply_text(msg)
        for u in db.all(): db.update({'points': 0}, User.id == u['id'])

    # --- الروليت المطور (بطل المسابقة + توب 10) ---
    elif full_text == "روليت":
        if is_owner or is_admin:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    elif full_text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif full_text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or is_owner:
            players = context.chat_data.get('r_players', [])
            if players:
                winner_raw = random.choice(players)
                w_id = winner_raw['id']
                w_db = db.get(User.id == w_id)
                new_wins = w_db.get('roulette_wins', 0) + 1
                db.update({'roulette_wins': new_wins}, User.id == w_id)
                
                # إعلان الفوز بالجولة
                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {winner_raw['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_wins} )\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                
                # فحص إذا وصل لـ 5 نقاط (بطل المسابقة)
                if new_wins >= 5:
                    final_msg = (
                        "👑👑👑 ملك الروليت 👑👑👑\n\n"
                        f"             👑 \" {winner_raw['name']} \" 👑\n\n"
                        f"       🔥🔥 \"{new_wins} نقاط\"🔥🔥"
                    )
                    await update.message.reply_text(final_msg)
                    # تصفير نقاط الروليت للجميع لبدء مسابقة جديدة
                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
            context.chat_data['r_on'] = False

    # --- قائمة توب 10 الروليت ---
    elif full_text == "توب الروليت":
        all_u = db.all()
        top_r = sorted(all_u, key=lambda x: x.get('roulette_wins', 0), reverse=True)[:10]
        msg = "🏆 **قائمة أساطير الروليت:**\n\n"
        icons = ["👑", "🔥", "♥️", "4-", "5-", "6-", "7-", "8-", "9-", "10-"]
        for i, u in enumerate(top_r):
            if u.get('roulette_wins', 0) > 0:
                icon = icons[i] if i < 3 else f"{i+1}-"
                msg += f"{icon} \" {u['name']} \" + ( {u['roulette_wins']} )\n"
        await update.message.reply_text(msg if len(top_r) > 0 else "لا يوجد نقاط مسجلة بعد.")

    elif full_text in ["العاب", "ألعاب"]:
        await update.message.reply_text("🎮 **قائمة الألعاب**\n💰 البنك: (رصيدي، راتب، هدية)\n🎲 التفاعل: (روليت، توب الروليت، ملك التفاعل)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
