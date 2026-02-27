import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User

async def handle_bank(update: Update, u_data, text, u_name, u_id):
    parts = text.split()
    cmd = parts[0] # الكلمة الأولى (استثمار، حظ، إلخ)

    # --- أوامر البنك التي تحتاج أرقام ---
    if cmd in ["استثمار", "حظ", "كنز", "مضاربة"]:
        if len(parts) < 2:
            await update.message.reply_text(f"⚠️ **عذراً يا ملك:** يجب كتابة المبلغ بجانب الأمر. مثال: `{cmd} 50000`")
            return True
        
        try:
            amount = int(parts[1])
        except ValueError:
            await update.message.reply_text("⚠️ **خطأ:** يرجى كتابة المبلغ بالأرقام فقط.")
            return True

        if amount <= 0:
            await update.message.reply_text("⚠️ **عذراً:** لا يمكن الاستثمار بمبلغ أقل من 1!")
            return True

        if u_data['balance'] < amount:
            await update.message.reply_text(f"❌ **عفواً يا ملك:** رصيدك الحالي ({u_data['balance']:,} د) لا يكفي لهذا الاستثمار.")
            return True

        if random.random() > 0.5: # ربح
            win_amt = amount # يربح ضعف ما وضع
            db.update({'balance': u_data['balance'] + win_amt}, User.id == u_id)
            await update.message.reply_text(f"📈 **عملية ناجحة:** استثمرت {amount:,} وربحت {win_amt:,} دينار! 🎉")
        else: # خسارة
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            await update.message.reply_text(f"📉 **خسارة فادحة:** فقدت {amount:,} دينار في {cmd}. حظاً أوفر!")
        return True

    # --- أوامر البنك الثابتة ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي المركزي**\n👤 الاسم: {u_name}\n💰 الرصيد: {u_data['balance']:,} دينار\n🏆 النقاط: {u_data['points']}")
        return True

    elif text in ["توب", "توب الاغنياء"]:
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u.get('name', 'لاعب')} ({u.get('balance', 0):,} د)\n"
        await update.message.reply_text(msg)
        return True

    elif text == "توب الحرامية":
        top = sorted(db.all(), key=lambda x: x.get('steal_count', 0), reverse=True)[:10]
        msg = "🥷 **أكبر 10 حرامية (محترفي الزرف):**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u.get('name', 'لاعب')} ({u.get('steal_count', 0)} زرفة)\n"
        await update.message.reply_text(msg)
        return True

    elif text == "راتب":
        now = time.time()
        if now - u_data.get('last_salary', 0) > 3600:
            sal = random.randint(500000, 1000000)
            db.update({'balance': u_data['balance'] + sal, 'last_salary': now}, User.id == u_id)
            await update.message.reply_text(f"💵 **مرسوم ملكي:** تم صرف راتب {sal:,} دينار.")
        else:
            rem = int((3600 - (now - u_data['last_salary'])) / 60)
            await update.message.reply_text(f"⏳ ارجع بعد {rem} دقيقة.")
        return True

    elif text == "بخشيش":
        tip = random.randint(50000, 150000)
        db.update({'balance': u_data['balance'] + tip}, User.id == u_id)
        await update.message.reply_text(f"🎁 استلمت بخشيش {tip:,} دينار.")
        return True

    elif text == "زرف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        t_data = db.get(User.id == target.id)
        if t_data and t_data.get('balance', 0) > 100000:
            amt = random.randint(10000, 100000)
            db.update({'balance': u_data['balance'] + amt, 'steal_count': u_data.get('steal_count', 0) + 1}, User.id == u_id)
            db.update({'balance': t_data['balance'] - amt}, User.id == target.id)
            await update.message.reply_text(f"🥷 زرفت {amt:,} من {target.first_name}!")
        return True

    return False
