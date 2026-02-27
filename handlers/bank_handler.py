import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User

async def handle_bank(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, u_name: str, u_id: int):
    u_data = await get_user_data(update)
    parts = text.split()
    cmd = parts[0] if parts else ""
    now = time.time()

    if cmd == "راتب":
        # تعديل الوقت لـ 30 دقيقة (1800 ثانية)
        if now - u_data.get('last_salary', 0) < 1800:
            rem = int((1800 - (now - u_data.get('last_salary', 0))) / 60)
            await update.message.reply_text(f"⏳ باقي {rem} دقيقة على راتبك يا {u_name}.")
            return True
        
        base_amt = random.randint(50000, 150000)
        tax = int(base_amt * 0.05)
        net_amt = base_amt - tax
        
        db.update({'balance': u_data['balance'] + net_amt, 'last_salary': now}, User.id == u_id)
        # ضريبة للمالك Anas
        owner_id = 5010882230 
        owner_data = db.get(User.id == owner_id)
        if owner_data:
            db.update({'balance': owner_data['balance'] + tax}, User.id == owner_id)

        await update.message.reply_text(f"💵 استلمت {base_amt:,} د.\n💰 ضريبة للمالك Anas: {tax:,} د.\n✅ الصافي: {net_amt:,} د.")
        return True

    if cmd == "حظ":
        # الحظ عشوائي بالكامل كما طلبت
        amt = random.randint(10000, 100000)
        win = random.choice([True, False])
        if win:
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            await update.message.reply_text(f"🎲 حظك عسل! ربحت {amt:,} د.")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == u_id)
            await update.message.reply_text(f"🎲 حظك تعبان.. خسرت {amt:,} د.")
        return True
    
    return False
