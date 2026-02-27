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
        
        # ... (باقي الأوامر تستدعي من BANK_MESSAGES بنفس الطريقة)
        db.update({'balance': u_data['balance'] + net_amt}, User.id == u_id)
        await update.message.reply_text(msg)
        return True
    
    # (باقي كود البنك كما هو مع ربطه بـ BANK_MESSAGES)
