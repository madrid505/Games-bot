import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from config import GROUP_IDS

async def bank_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in GROUP_IDS or not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    u_data = await get_user_data(update)

    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف ميسك المركزي**\n👤 الاسم: {user_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
    
    elif text == "توب":
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u['name']} ({u['balance']:,} د)\n"
        await update.message.reply_text(msg)

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            salary = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + salary, 'last_salary': now}, User.id == user_id)
            await update.message.reply_text(f"💵 **المرسوم الملكي:** تم إيداع راتبك وقدره {salary:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ ارجع بعد {rem} دقيقة لاستلام الراتب.")

    elif text == "بخشيش":
        tip = random.randint(50000, 150000)
        db.update({'balance': u_data['balance'] + tip}, User.id == user_id)
        await update.message.reply_text(f"🎁 **بخشيش ملكي:** استلمت {tip:,} دينار.")

    elif text.startswith("هدية") and update.message.reply_to_message:
        try:
            amt = int(text.split()[1])
            target_id = update.message.reply_to_message.from_user.id
            if u_data['balance'] >= amt > 0:
                t_data = await get_user_data(update.message.reply_to_message)
                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
                db.update({'balance': t_data['balance'] + amt}, User.id == target_id)
                await update.message.reply_text(f"🎁 تم إرسال {amt:,} دينار هدية إلى {update.message.reply_to_message.from_user.first_name}.")
        except: pass

    elif text in ["حظ", "استثمار", "مضاربة"]:
        amt = random.randint(100000, 1000000)
        if random.random() > 0.5:
            db.update({'balance': u_data['balance'] + amt}, User.id == user_id)
            await update.message.reply_text(f"📈 **ربحت!** في {text} كسبت {amt:,} دينار.")
        else:
            db.update({'balance': max(0, u_data['balance'] - amt)}, User.id == user_id)
            await update.message.reply_text(f"📉 **خسرت!** في {text} فقدت {amt:,} دينار.")
