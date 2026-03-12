import random
import time
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from config import OWNER_ID
from royal_messages import BANK_STATUS

async def handle_bank(update: Update, u_data, text, u_name, u_id):
    parts = text.split()
    if not parts: return False
    cmd = parts[0].strip()

    # 🏦 دالة إدارة الضرائب الملكية (تخصم 10% وتحولها للمالك)
    async def apply_tax(amount):
        tax = int(amount * 0.10)
        net_amount = amount - tax
        owner_exists = db.get(User.id == OWNER_ID)
        if owner_exists:
            db.update({'balance': owner_exists.get('balance', 0) + tax}, User.id == OWNER_ID)
        return net_amount, tax

    # --- 💰 أوامر المنح الملكية ---
    if cmd in ["راتب", "كنز", "بخشيش", "حظ"]:
        now = time.time()
        
        if cmd == "راتب":
            last_s = u_data.get('last_salary', 0)
            if now - last_s < 1800:
                rem = int((1800 - (now - last_s)) / 60)
                await update.message.reply_text(f"⏳ **مهلاً يا ملك:** الراتب يُصرف كل 30 دقيقة. ارجع بعد {rem} دقيقة.")
                return True
            base_amt = random.randint(500000, 1000000)
            db.update({'last_salary': now}, User.id == u_id)
        
        elif cmd == "كنز":
            base_amt = random.randint(200000, 500000)
        
        elif cmd == "حظ":
            base_amt = random.randint(100000, 800000)
            if random.random() < 0.4:
                loss = base_amt // 2
                db.update({'balance': max(0, u_data['balance'] - loss)}, User.id == u_id)
                await update.message.reply_text(f"📉 **عثرة حظ:** تعثرت في السوق وفقدت {loss:,} دينار.")
                return True
        else: # بخشيش
            base_amt = random.randint(50000, 150000)

        net_amt, tax_amt = await apply_tax(base_amt)
        db.update({'balance': u_data['balance'] + net_amt}, User.id == u_id)
        
        msgs = {
            "راتب": f"💵 **مرسوم ملكي:** استلمت راتبك {base_amt:,} د.\n⚖️ ضريبة (Anas): {tax_amt:,} د | الصافي: {net_amt:,} د.",
            "كنز": f"💎 **ثراء مفاجئ:** وجدت كنزاً بقيمة {base_amt:,} د.\n⚖️ ضريبة (Anas): {tax_amt:,} د | الصافي: {net_amt:,} د.",
            "بخشيش": f"🎁 **هبة:** استلمت بخشيش بقيمة {base_amt:,} د.\n⚖️ ضريبة (Anas): {tax_amt:,} د | الصافي: {net_amt:,} د.",
            "حظ": f"🎲 **ضربة معلم:** ربحت في الحظ {base_amt:,} د.\n⚖️ ضريبة (Anas): {tax_amt:,} د | الصافي: {net_amt:,} د."
        }
        await update.message.reply_text(msgs[cmd])
        return True

    # --- 📈 أوامر الاستثمار والمخاطرة ---
    if cmd in ["استثمار", "مضاربة"]:
        if len(parts) < 2:
            await update.message.reply_text(f"⚠️ **تنبيه:** أرسل المبلغ بجانب الأمر. مثال: `{cmd} 50000`")
            return True
        try:
            amount = int(parts[1])
        except: return True

        if amount <= 0 or u_data['balance'] < amount:
            await update.message.reply_text("❌ **فشل العملية:** رصيدك لا يكفي لهذه المخاطرة.")
            return True

        if random.random() > 0.5:
            net_win, tax_amt = await apply_tax(amount)
            db.update({'balance': u_data['balance'] + net_win}, User.id == u_id)
            await update.message.reply_text(f"📈 **بورصة مونوبولي:** استثمار ناجح! ربحت {amount:,} د.\n⚖️ ضريبة (Anas): {tax_amt:,} د | الصافي: {net_win:,} د.")
        else:
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            await update.message.reply_text(f"📉 **انتكاسة:** خسر مشروعك {amount:,} دينار في ال{cmd}.")
        return True

    # --- 🎁 نظام الهدايا ---
    if cmd == "هدية" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if target.is_bot: return True
        try:
            amount = int(parts[1])
            if amount <= 0 or u_data['balance'] < amount: raise ValueError
        except:
            await update.message.reply_text("⚠️ **عفواً:** حدد مبلغاً صحيحاً من رصيدك لتقديمه كهدية.")
            return True

        t_data = db.get(User.id == target.id)
        if t_data:
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            db.update({'balance': t_data['balance'] + amount}, User.id == target.id)
            await update.message.reply_text(f"🎁 **كرم ملكي:** منح {u_name} هدية إلى {target.first_name} بقيمة {amount:,} د.")
        return True

    # --- 📊 الاستعلامات والترتيب ---
    if text == "رصيدي":
        # الربط مع القالب الملكي من ملف royal_messages.py
        msg = BANK_STATUS.format(
            u_name=u_name,
            balance=u_data['balance'],
            points=u_data.get('points', 0),
            img_points=u_data.get('image_points', 0),
            weekly_pts=u_data.get('weekly_pts', 0)
        )
        await update.message.reply_text(msg)
        return True

    if text in ["توب", "توب الاغنياء"]:
        top = sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:10]
        msg = "🏆 **قائمة هوامير مونوبولي (الأكثر ثراءً):**\n\n"
        for i, u in enumerate(top, 1):
            msg += f"{i} ⮕ **{u.get('name', 'لاعب')}**\n💰 `{u.get('balance', 0):,}` دينار\n"
        await update.message.reply_text(msg)
        return True

    if text == "زرف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        t_data = db.get(User.id == target.id)
        if t_data and t_data.get('balance', 0) > 100000:
            amt = random.randint(10000, 100000)
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            db.update({'balance': t_data['balance'] - amt}, User.id == target.id)
            await update.message.reply_text(f"🥷 **عملية احترافية:** زرفت {amt:,} من {target.first_name}!")
        else:
            await update.message.reply_text("❌ **فشل الزرف:** الضحية لا تملك ما يكفي أو أنها تحت حماية المملكة!")
        return True

    return False
