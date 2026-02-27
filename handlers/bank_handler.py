import random, time
from telegram import Update
from db import db, User
from config import OWNER_ID
from strings import BANK_MESSAGES

async def handle_bank(update: Update, u_data, text, u_name, u_id):
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

    # أمر زرف (يجب أن يكون رداً على رسالة)
    if cmd == "زرف":
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ يجب أن يكون الزرف رداً على رسالة الشخص!")
            return True
        target = update.message.reply_to_message.from_user
        if target.id == u_id: return True
        t_data = db.get(User.id == target.id)
        if t_data and t_data.get('balance', 0) > 1000:
            amt = random.randint(1000, 50000)
            db.update({'balance': u_data['balance'] + amt}, User.id == u_id)
            db.update({'balance': t_data['balance'] - amt}, User.id == target.id)
            await update.message.reply_text(BANK_MESSAGES["steal"].format(amt=amt, target_name=target.first_name))
        else:
            await update.message.reply_text("❌ هذا الشخص طفران ما معه شيء تزرفه!")
        return True

    # أوامر الراتب، كنز، بخشيش، حظ
    if cmd in ["راتب", "كنز", "بخشيش", "حظ"]:
        now = time.time()
        if cmd == "راتب":
            if now - u_data.get('last_salary', 0) < 1800:
                rem = int((1800 - (now - u_data['last_salary'])) / 60)
                await update.message.reply_text(f"⏳ ارجع بعد {rem} دقيقة.")
                return True
            base_amt = random.randint(500000, 1000000)
            db.update({'last_salary': now}, User.id == u_id)
            net_amt, tax_amt = await apply_tax(base_amt)
            msg = BANK_MESSAGES["salary"].format(base_amt=base_amt, tax_amt=tax_amt, net_amt=net_amt)
        elif cmd == "حظ":
            base_amt = random.randint(100000, 800000)
            if random.random() < 0.4:
                loss = base_amt // 2
                db.update({'balance': max(0, u_data['balance'] - loss)}, User.id == u_id)
                await update.message.reply_text(BANK_MESSAGES["luck_loss"].format(loss_amt=loss))
                return True
            net_amt, tax_amt = await apply_tax(base_amt)
            msg = BANK_MESSAGES["luck_win"].format(base_amt=base_amt, tax_amt=tax_amt, net_amt=net_amt)
        elif cmd == "كنز":
            base_amt = random.randint(200000, 500000)
            net_amt, tax_amt = await apply_tax(base_amt)
            msg = BANK_MESSAGES["treasure"].format(base_amt=base_amt, tax_amt=tax_amt, net_amt=net_amt)
        else: # بخشيش
            base_amt = random.randint(50000, 150000)
            net_amt, tax_amt = await apply_tax(base_amt)
            msg = BANK_MESSAGES["tip"].format(base_amt=base_amt, tax_amt=tax_amt, net_amt=net_amt)

        db.update({'balance': u_data['balance'] + net_amt}, User.id == u_id)
        await update.message.reply_text(msg)
        return True

    # أوامر استثمار، مضاربة، هدية
    if cmd in ["استثمار", "مضاربة", "هدية"]:
        if len(parts) < 2: return False
        try: amount = int(parts[1])
        except: return False

        if amount <= 0 or u_data['balance'] < amount:
            await update.message.reply_text("❌ رصيدك لا يكفي.")
            return True

        if cmd == "هدية" and update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            t_data = db.get(User.id == target.id)
            if t_data:
                db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
                db.update({'balance': t_data.get('balance', 0) + amount}, User.id == target.id)
                await update.message.reply_text(BANK_MESSAGES["gift"].format(u_name=u_name, t_name=target.first_name, amount=amount))
            return True

        if random.random() > 0.5:
            win_amt = amount
            net_win, tax_amt = await apply_tax(win_amt)
            db.update({'balance': u_data['balance'] + net_win}, User.id == u_id)
            await update.message.reply_text(BANK_MESSAGES["invest_win"].format(win_amt=win_amt, tax_amt=tax_amt, net_win=net_win))
        else:
            db.update({'balance': u_data['balance'] - amount}, User.id == u_id)
            await update.message.reply_text(BANK_MESSAGES["invest_loss"].format(amount=amount, cmd=cmd))
        return True

    if text == "رصيدي":
        await update.message.reply_text(f"💰 **رصيدك:** {u_data['balance']:,} د | 🏆 **نقاطك:** {u_data['points']}")
        return True

    return False
