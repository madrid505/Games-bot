import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# قاعدة البيانات (لضمان عدم التصفير)
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
        # الرصيد الأولي للمستخدمين الجدد فقط
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({
            'id': user_id, 
            'name': update.effective_user.first_name, 
            'balance': balance, 
            'points': 0, 
            'wins': 0, 
            'stolen_total': 0,
            'last_salary': 0, 
            'last_rob': 0, 
            'last_treasure': 0, 
            'last_luck': 0
        })
        user_data = db.get(User.id == user_id)
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
    
    # تحديث النقاط تلقائياً مع كل رسالة (لنظام ملك التفاعل)
    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)

    # --- 1. التحكم في الألعاب ---
    if full_text in ["فتح", "فتح الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['active'] = True
            await update.message.reply_text("✅ تم فتح الألعاب والبنك بنجاح!")
        return

    if full_text in ["قفل", "قفل الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['active'] = False
            await update.message.reply_text("🔒 تم قفل الألعاب.")
        return

    # --- 2. أوامر البنك الكاملة ---
    if cmd == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} ريال\n⭐ نقاطك: {u_data.get('points', 0)}")

    elif cmd == "راتب":
        if current_time - u_data.get('last_salary', 0) > 600:
            amt = random.randint(5000000, 15000000)
            db.update({'balance': u_data['balance'] + amt, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الراتب متاح كل 10 دقائق")

    elif cmd == "كنز":
        if current_time - u_data.get('last_treasure', 0) > 3600:
            amt = random.randint(50000000, 150000000)
            db.update({'balance': u_data['balance'] + amt, 'last_treasure': current_time}, User.id == user_id)
            await update.message.reply_text(f"💎 مبروك وجدت كنزاً: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الكنز متاح كل ساعة")

    elif cmd == "زرف":
        if current_time - u_data.get('last_rob', 0) > 300:
            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 50000000]
            if others:
                target = random.choice(others)
                amt = random.randint(1000000, 10000000)
                db.update({'balance': u_data['balance'] + amt, 'last_rob': current_time, 'stolen_total': u_data.get('stolen_total', 0) + amt}, User.id == user_id)
                db.update({'balance': target['balance'] - amt}, User.id == target['id'])
                await update.message.reply_text(f"🥷 زرفت {amt:,} ريال من {target['name']}")
        else: await update.message.reply_text("⏳ الزرف كل 5 دقائق")

    elif cmd == "حظ":
        if current_time - u_data.get('last_luck', 0) > 60:
            amt = random.randint(1000000, 30000000)
            if random.random() > 0.5:
                db.update({'balance': u_data['balance'] + amt, 'last_luck': current_time}, User.id == user_id)
                await update.message.reply_text(f"🍀 حظك حلو! كسبت {amt:,} ريال")
            else:
                db.update({'balance': max(0, u_data['balance'] - amt), 'last_luck': current_time}, User.id == user_id)
                await update.message.reply_text(f"💀 حظك سيء.. خسرت {amt:,} ريال")
        else: await update.message.reply_text("⏳ الحظ كل دقيقة")

    elif cmd == "هدية" and len(parts) > 1 and update.message.reply_to_message:
        try:
            gift = int(parts[1])
            target_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= gift > 0:
                target_data = db.get(User.id == target_id)
                if target_data:
                    db.update({'balance': u_data['balance'] - gift}, User.id == user_id)
                    db.update({'balance': target_data['balance'] + gift}, User.id == target_id)
                    await update.message.reply_text(f"🎁 تم إرسال {gift:,} ريال كهدية إلى {target_data['name']}")
        except: pass

    elif cmd == "توب":
        all_u = db.all()
        if "الاغنياء" in full_text:
            top = sorted(all_u, key=lambda x: x.get('balance', 0), reverse=True)[:5]
            msg = "💰 **توب الأغنياء:**\n" + "\n".join([f"{i+1}- {u['name']} : {u['balance']:,}" for i, u in enumerate(top)])
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif "الحرامية" in full_text:
            top = sorted(all_u, key=lambda x: x.get('stolen_total', 0), reverse=True)[:5]
            msg = "🥷 **توب الحرامية:**\n" + "\n".join([f"{i+1}- {u['name']} : {u['stolen_total']:,}" for i, u in enumerate(top)])
            await update.message.reply_text(msg, parse_mode="Markdown")

    # --- 3. ملك التفاعل (الرسالة الملكية) ---
    elif full_text == "ملك التفاعل" and (is_owner or is_admin):
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

    # --- 4. الروليت (تكرار انا + نقاط الفوز التراكمية) ---
    elif full_text == "روليت":
        if is_owner or is_admin:
            context.chat_data['r_on'] = True
            context.chat_data['r_players'] = []
            context.chat_data['r_starter'] = user_id
            await update.message.reply_text("🔥🔥 بدأت الروليت.. اكتب انا للتسجيل (التكرار مسموح)")

    elif full_text == "انا" and context.chat_data.get('r_on'):
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢 تم تسجيلك يا بطل")

    elif full_text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or is_owner:
            players = context.chat_data.get('r_players', [])
            if players:
                winner_raw = random.choice(players)
                w_id = winner_raw['id']
                # تحديث الفوز التراكمي في الداتابيز
                curr_wins = db.get(User.id == w_id).get('wins', 0) + 1
                db.update({'wins': curr_wins}, User.id == w_id)
                
                win_msg = (
                    "👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n"
                    f"          👑 \" {winner_raw['name']} \" 👑\n\n"
                    f"🏆 فوزك رقم: ( {curr_wins} )\n\n"
                    "👈👈 استمر معنا بالمشاركة 👉👉"
                )
                await update.message.reply_text(win_msg)
            context.chat_data['r_on'] = False

    # --- 5. قائمة الألعاب (العاب) ---
    elif full_text in ["العاب", "ألعاب"]:
        menu = (
            "🎮 **قائمة ألعاب مونوبولي العظيم** 🎮\n\n"
            "💰 **البنك:** (رصيدي، راتب، كنز، زرف، حظ، هدية، توب الاغنياء)\n"
            "🎲 **التفاعل:** (روليت، ملك التفاعل)\n"
            "⚙️ **التحكم:** (فتح، قفل)"
        )
        await update.message.reply_text(menu, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
