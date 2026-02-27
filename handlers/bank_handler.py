import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from strings import BANK_MESSAGES

async def handle_bank(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, u_name: str, u_id: int):
    # جلب بيانات المستخدم هنا داخلياً لضمان الدقة
    u_data = await get_user_data(update)
    parts = text.split()
    cmd = parts[0] if parts else ""
    now = time.time()

    # 1. أمر الراتب
    if cmd == "راتب":
        if now - u_data.get('last_salary', 0) < 1800:
            await update.message.reply_text(f"⏳ يا {u_name}، ما تقدر تاخذ راتب الحين. ارجع بعد شوي!")
            return True
        
        base_amt = random.randint(50000, 150000)
        # تحديث البيانات
        db.update({
            'balance': u_data['balance'] + base_amt,
            'last_salary': now
        }, User.id == u_id)
        
        await update.message.reply_text(f"💵 تم صرف راتبك: {base_amt:,} د.")
        return True

    # 2. أمر الرصيد
    if cmd in ["رصيدي", "فلوسي", "الرصيد"]:
        await update.message.reply_text(f"💰 **رصيدك الحالي:** {u_data['balance']:,} د.")
        return True

    # 3. أمر الزرف (يحتاج رد على رسالة)
    if cmd == "زرف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if target.id == u_id:
            return True
        
        t_data = db.get(User.id == target.id)
        if t_data and t_data.get('balance', 0) > 1000:
            amt = random.randint(1000, 50000)
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            db.update({'balance': t_data['balance'] - amt}, User.id == target.id)
            await update.message.reply_text(f"🥷 زرفت {amt:,} د من {target.first_name}!")
        return True

    return False
