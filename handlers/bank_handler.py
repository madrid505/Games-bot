import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from config import OWNER_ID

async def handle_bank(update: Update, u_data, text, u_name, u_id):
    parts = text.split()
    cmd = parts[0].strip()

    # دالة إدارة الضرائب (تخصم 10% وتحولها للمالك Anas)
    async def apply_tax(amount):
        tax = int(amount * 0.10)
        net_amount = amount - tax
        # إضافة الضريبة للمالك Anas
        owner_data = db.get(User.id == OWNER_ID)
        if owner_data:
            db.update({'balance': owner_data.get('balance', 0) + tax}, User.id == OWNER_ID)
        return net_amount, tax

    # --- أوامر المبالغ العشوائية (تكتب الكلمة فقط) ---
    if cmd in ["راتب", "كنز", "بخشيش", "حظ"]:
        now = time.time()
        
        # تعديل وقت الراتب إلى 30 دقيقة (1800 ثانية)
        if cmd == "راتب":
            if now - u_data.get('last_salary', 0) < 1800:
                rem = int((1800 - (now - u_data['last_salary'])) / 60)
                await update.message.reply_text(f"⏳ **مهلاً يا ملك:** ارجع بعد {rem} دقيقة لاستلام راتبك.")
                return True
            base_amt = random.randint(500000, 1000000)
            db.update({'last_salary': now}, User.id == u_id)
        
        elif cmd == "كنز":
            base_amt = random.randint(200000, 500000)
        
        elif cmd == "حظ":
            # جعل الحظ عشوائياً بالكامل (ربح أو خسارة بمبالغ كبيرة)
            base_amt = random.randint(100000, 800000)
            if random.random() < 0.4: # نسبة خسارة في الحظ 40%
                db.update({'balance': max(0, u_data['balance'] - (base_amt // 2))}, User.id == u_id)
                await update.message.reply_text(f"📉 **يا لسوء الحظ!** تعثرت وفقدت {(base_amt // 2):,} دينار.")
                return True
        
        else: # بخشيش
            base_amt = random.randint(50000, 150000)

        net_amt, tax_amt = await apply_tax(base_amt)
        db.update({'balance': u_data['balance'] + net_amt}, User.id == u_id)
        
        msgs = {
            "راتب": f"💵 **مرسوم ملكي:** استلمت راتبك {base_amt:,} د. (ضريبة للمالك Anas: {tax_amt:,} د). الصافي: {net_amt:,} د.",
            "كنز": f"💎 **يا بطل:** وجدت كنزاً بقيمة {base_amt:,} د. (ضريبة للمالك Anas: {tax_amt:,} د). الصافي: {net_amt:,} د.",
            "بخشيش": f"🎁 **بخشيش:** استلمت {base_amt:,} د. (ضريبة للمالك Anas: {tax_amt:,} د). الصافي: {net_amt:,} د.",
            "حظ": f"🎲 **ضربة حظ!** ربحت {base_amt:,} د. (ضريبة للمالك Anas: {tax_amt:,} د). الصافي: {net_amt:,} د."
        }
        await update.message.reply_text(msgs[cmd])
        return True

    # --- أوامر الاستثمار والمخاطرة (تحتاج رقم بجانبها) ---
    if cmd in ["استثمار", "مضاربة"]:
        if len(parts) < 2:
            await update.message.reply_text(f"⚠️ اكتب المبلغ بجانب الأمر. مثال: `{cmd} 50000`")
            return True
        try:
            amount = int(parts[1])
        except: return True

        if amount <= 0 or u_data['balance'] < amount:
            await update.message.reply_text("❌ رصيدك لا يكفي أو المبلغ غير صحيح.")
            return True

        if random.random() > 0.5: # ربح
            win_amt = amount
            net_win, tax_amt = await apply_tax(win_amt)
            db.update({'balance': u_data['balance'] + net_win}, User.id == u_id)
            await update.message.reply_text(f"📈 **استثمار ناجح:** ربحت {win_amt:,} د. (ضريبة للمالك Anas بنسبة 10%: {tax_amt:,} د). الصافي: {net_win:,} د.")
        else: # خسارة
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            await update.message.reply_text(f"📉 **للأسف:** خسرت {amount:,} دينار في ال{cmd}.")
        return True

    # --- أمر هدية (تحويل رصيد بالرد) ---
    if cmd == "هدية" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if target.is_bot or len(parts) < 2: return True
        try:
            amount = int(parts[1])
            if amount <= 0 or u_data['balance'] < amount: raise ValueError
        except:
            await update.message.reply_text("⚠️ اكتب مبلغاً صحيحاً تملكه بعد كلمة هدية.")
            return True

        t_data = db.get(User.id == target.id)
        if t_data:
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            db.update({'balance': t_data['balance'] + amount}, User.id == target.id)
            await update.message.reply_text(f"🎁 **هدية ملكية:** من {u_name} إلى {target.first_name} بقيمة {amount:,} د.")
        return True

    # --- الأوامر العامة ---
    if text == "رصيدي":
        await update.message.reply_text(f"🏦 **مصرف مونوبولي**\n👤 {u_name}\n💰 رصيدك: {u_data['balance']:,} د\n🏆 نقاطك: {u_data['points']}")
        return True
    elif text in ["توب", "توب الاغنياء"]:
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **أغنى 10 هوامير في مونوبولي:**\n\n"
        for i, u in enumerate(top, 1): msg += f"{i} - {u.get('name', 'لاعب')} ({u.get('balance', 0):,} د)\n"
        await update.message.reply_text(msg)
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
