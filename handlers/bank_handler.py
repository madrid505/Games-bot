import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User

async def handle_bank(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, u_name: str, u_id: int):
    # جلب البيانات هنا لضمان عدم حدوث خطأ CallbackContext
    u_data = await get_user_data(update)
    parts = text.split()
    cmd = parts[0] if parts else ""
    now = time.time()

    # --- أمر الراتب (كل 30 دقيقة) ---
    if cmd == "راتب":
        last_s = u_data.get('last_salary', 0)
        if now - last_s < 1800:
            rem = int((1800 - (now - last_s)) / 60)
            await update.message.reply_text(f"⏳ باقي {rem} دقيقة على راتبك يا {u_name}.")
            return True
        
        base_amt = random.randint(50000, 150000)
        tax = int(base_amt * 0.05)
        net_amt = base_amt - tax
        
        # تحديث رصيد المستخدم والوقت
        db.update({'balance': u_data['balance'] + net_amt, 'last_salary': now}, User.id == u_id)
        
        # تحويل الضريبة للمالك Anas (آيدي: 5010882230)
        owner_id = 5010882230
        owner_data = db.get(User.id == owner_id)
        if owner_data:
            db.update({'balance': owner_data['balance'] + tax}, User.id == owner_id)

        await update.message.reply_text(
            f"💵 استلمت {base_amt:,} د.\n"
            f"💰 ضريبة للمالك Anas: {tax:,} د.\n"
            f"✅ الصافي لك: {net_amt:,} د."
        )
        return True

    # --- أمر الحظ (عشوائي بالكامل) ---
    if cmd == "حظ":
        amt = random.randint(10000, 100000)
        win = random.choice([True, False])
        
        if win:
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            await update.message.reply_text(f"🎲 حظك يكسر الصخر! ربحت {amt:,} د.")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == u_id)
            await update.message.reply_text(f"🎲 الحظ تعبان.. خسرت {amt:,} د.")
        return True

    # --- أمر الرصيد ---
    if cmd in ["رصيدي", "رصيد", "فلوسي"]:
        await update.message.reply_text(f"💰 **رصيدك الملكي:** {u_data['balance']:,} د.")
        return True

    return False
