import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from config import OWNER_ID

async def handle_bank(update: Update, u_data, text, u_name, u_id):
    # تنظيف النص وفصل الكلمات
    parts = text.split()
    if not parts: return False
    cmd = parts[0].strip()

    async def apply_tax(amount):
        tax = int(amount * 0.10)
        net_amount = amount - tax
        owner_data = db.get(User.id == OWNER_ID)
        if owner_data:
            db.update({'balance': owner_data.get('balance', 0) + tax}, User.id == OWNER_ID)
        return net_amount, tax

    # --- أوامر ثابتة وعشوائية ---
    if cmd in ["راتب", "كنز", "بخشيش", "حظ"]:
        now = time.time()
        if cmd == "راتب":
            if now - u_data.get('last_salary', 0) < 1800:
                rem = int((1800 - (now - u_data['last_salary'])) / 60)
                await update.message.reply_text(f"⏳ **مهلاً يا ملك:** ارجع بعد {rem} دقيقة.")
                return True
            base_amt = random.randint(500000, 1000000)
            db.update({'last_salary': now}, User.id == u_id)
        elif cmd == "كنز":
            base_amt = random.randint(200000, 500000)
        elif cmd == "حظ":
            base_amt = random.randint(100000, 800000)
            if random.random() < 0.4:
                db.update({'balance': max(0, u_data['balance'] - (base_amt // 2))}, User.id == u_id)
                await update.message.reply_text(f"📉 **سوء حظ:** فقدت {(base_amt // 2):,} د.")
                return True
        else: # بخشيش
            base_amt = random.randint(50000, 150000)

        net_amt, tax_amt = await apply_tax(base_amt)
        db.update({'balance': u_data['balance'] + net_amt}, User.id == u_id)
        
        msgs = {
            "راتب": f"💵 استلمت راتبك {base_amt:,} د. (ضريبة Anas: {tax_amt:,} د). الصافي: {net_amt:,} د.",
            "كنز": f"💎 وجدت كنزاً بقيمة {base_amt:,} د. (ضريبة Anas: {tax_amt:,} د). الصافي: {net_amt:,} د.",
            "بخشيش": f"🎁 استلمت بخشيش {base_amt:,} د. (ضريبة Anas: {tax_amt:,} د).",
            "حظ": f"🎲 ضربة حظ! ربحت {base_amt:,} د. (ضريبة Anas: {tax_amt:,} د)."
        }
        await update.message.reply_text(msgs[cmd])
        return True

    # --- أوامر تحتاج رقم (استثمار، مضاربة، هدية) ---
    if cmd in ["استثمار", "مضاربة", "هدية"]:
        if len(parts) < 2:
            if cmd != "هدية": await update.message.reply_text(f"⚠️ اكتب المبلغ بجانب {cmd}.")
            return True
        try:
            amount = int(parts[1])
        except: return True

        if amount <= 0 or u_data['balance'] < amount:
            await update.message.reply_text("❌ رصيدك لا يكفي.")
            return True

        if cmd == "هدية" and update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            t_data = db.get(User.id == target.id)
            if t_data:
                db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
                db.update({'balance': t_data['balance'] + amount}, User.id == target.id)
                await update.message.reply_text(f"🎁 هدية من {u_name} إلى {target.first_name} بقيمة {amount:,} د.")
            return True

        if random.random() > 0.5:
            win_amt = amount
            net_win, tax_amt = await apply_tax(win_amt)
            db.update({'balance': u_data['balance'] + net_win}, User.id == u_id)
            await update.message.reply_text(f"📈 ربحت {win_amt:,} د. (ضريبة Anas: {tax_amt:,} د). الصافي: {net_win:,} د.")
        else:
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            await update.message.reply_text(f"📉 خسرت {amount:,} د.")
        return True

    if text == "رصيدي":
        await update.message.reply_text(f"💰 رصيدك: {u_data['balance']:,} د | نقاطك: {u_data['points']}")
        return True
    
    return False
