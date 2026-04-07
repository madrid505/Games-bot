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
            "راتب": (
                f"🏦 **【 كـشـف حـسـاب الـبـنـك 】**\n"
                f"━━━━━━━━━━━━━━\n"
                f"📜 **الـبـيـان:** إيـداع الـراتـب الـدوري\n"
                f"💵 **الـمـبلـغ:** `{base_amt:,}` د\n"
                f"⚖️ **الـضـريـبـة:** `-{tax_amt:,}` د\n"
                f"🏛️ **الخزينة:** ༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻\n"
                f"────────────────\n"
                f"✨ **الـرصـيـد الـمُـرحـل:** ✨\n"
                f"💰 ⮕ ` {net_amt:,} ` ديـنـار\n"
                f"━━━━━━━━━━━━━━"
            ),
            "كنز": (
                f"🏦 **【 كـشـف حـسـاب الـبـنـك 】**\n"
                f"━━━━━━━━━━━━━━\n"
                f"💎 **الـبـيـان:** تـحـويـل مـن كـنـز مـدفـون\n"
                f"💰 **الـقـيـمـة:** `{base_amt:,}` د\n"
                f"⚖️ **الـضـريـبـة:** `-{tax_amt:,}` د\n"
                f"🏛️ **الخزينة:** ༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻\n"
                f"────────────────\n"
                f"🏆 **الـمـبـلـغ الـمُـودع:**\n"
                f"✨ ⮕ ` {net_amt:,} ` ديـنـار\n"
                f"━━━━━━━━━━━━━━"
            ),
            "بخشيش": (
                f"🏦 **【 كـشـف حـسـاب الـبـنـك 】**\n"
                f"━━━━━━━━━━━━━━\n"
                f"🎁 **الـبـيـان:** هـبـة مـن الـديـوان\n"
                f"💸 **الـمـبـلـغ:** `{base_amt:,}` د\n"
                f"⚖️ **الـضـريـبـة:** `-{tax_amt:,}` د\n"
                f"🏛️ **الخزينة:** ༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻\n"
                f"────────────────\n"
                f"✅ **الـحـركـة الـمـالـيـة:**\n"
                f"✨ ⮕ ` {net_amt:,} ` ديـنـار\n"
                f"━━━━━━━━━━━━━━"
            ),
            "حظ": (
                f"🏦 **【 كـشـف حـسـاب الـبـنـك 】**\n"
                f"━━━━━━━━━━━━━━\n"
                f"🎲 **الـبـيـان:** أربـاح مـن صـندوق الـحـظ\n"
                f"📈 **الـنـتـيـجـة:** `{base_amt:,}` د\n"
                f"⚖️ **الـضـريـبـة:** `-{tax_amt:,}` د\n"
                f"🏛️ **الخزينة:** ༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻\n"
                f"────────────────\n"
                f"💰 **الـصـافـي الـنـهائـي:**\n"
                f"✨ ⮕ ` {net_amt:,} ` ديـنـار\n"
                f"━━━━━━━━━━━━━━"
            )
                }
        
        
        await update.message.reply_text(msgs[cmd])
        return True

    # --- 📈 أوامر الاستثمار والمخاطرة المحدثة ---
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

        old_balance = u_data['balance']

        if random.random() > 0.5:
            # حالة الربح
            net_win, tax_amt = await apply_tax(amount)
            new_balance = old_balance + net_win
            db.update({'balance': new_balance}, User.id == u_id)
            
            win_msg = (
                "📈 **【 كـشـف حـسـاب : بـورصـة مـونـوبـولـي 】**\n"
                "━━━━━━━━━━━━━━\n"
                "✨ **الـبـيـان:** اسـتـثـمار نـاجـح\n"
                f"💰 **الـرصـيـد الـسـابـق:** `{old_balance:,}` د\n"
                f"💵 **أربـاح الـعـمـلـيـة:** `{amount:,}` د\n"
                f"🏛️ **الخزينة:** ༺۝༒♛ 🅰🅽🅰🆂 ♛༒۝༻\n"
                f"⚖️ **ضـريـبـة الـتـداول:** `-{tax_amt:,}` د\n"
                "────────────────\n"
                "📥 **الـصـافـي الـمُـسـتـلـم:** ✨\n"
                f"✅ ⮕ ` {net_win:,} ` ديـنـار\n"
                "────────────────\n"
                f"💳 **الـرصـيـد الـحـالـي:** `{new_balance:,}` د\n"
                "━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(win_msg)
        else:
            # حالة الخسارة
            new_balance = old_balance - amount
            db.update({'balance': new_balance}, User.id == u_id)
            
            loss_msg = (
                "📉 **【 كـشـف حـسـاب : بـورصـة مـونـوبـولـي 】**\n"
                "━━━━━━━━━━━━━━\n"
                "❌ **الـبـيـان:** خسارة مـالـيـة\n"
                f"💰 **الـرصـيـد الـسـابـق:** `{old_balance:,}` د\n"
                f"💸 **خـسـارة الـمـشـروع:** `-{amount:,}` د\n"
                "────────────────\n"
                "🛑 **الـتـأثـيـر:** تـم خـصـم الـمـبـلـغ\n"
                "────────────────\n"
                f"💳 **الـرصـيـد الـحـالـي:** `{new_balance:,}` د\n"
                "━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(loss_msg)
        return True
            

    # --- 🎁 نظام الهدايا المطور (كشف تحويل بنكي) ---
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
            # حساب الأرصدة الجديدة
            old_balance = u_data['balance']
            new_balance = old_balance - amount
            target_new_balance = t_data['balance'] + amount

            # تحديث قاعدة البيانات
            db.update({'balance': new_balance}, User.id == u_id)
            db.update({'balance': target_new_balance}, User.id == target.id)
            
            gift_msg = (
                "🏦 **【 كـشـف حـسـاب : تـحـويـل صـادر 】**\n"
                "━━━━━━━━━━━━━━\n"
                "🎁 **الـبـيـان:** مـنـح هـديـة مـلـكـيـة\n"
                f"👤 **إلـى:** `{target.first_name}`\n"
                "────────────────\n"
                f"💰 **الـرصـيـد الـسـابـق:** `{old_balance:,}` د\n"
                f"💸 **الـمـبـلـغ الـمُـحول:** `-{amount:,}` د\n"
                "────────────────\n"
                "✨ **حـالـة الـعـمـلـيـة:** تـم الـتـحـويـل بـنـجـاح\n"
                f"✅ ⮕ ` {u_name} ` ❤️ ` {target.first_name} `\n"
                "────────────────\n"
                f"💳 **الـرصـيـد الـحـالـي:** `{new_balance:,}` د\n"
                "━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(gift_msg)
        return True
            

    # --- 📊 كشف الحساب العام (رصيدي) ---
    if text == "رصيدي":
        # تصميم كشف الحساب الشامل
        msg = (
            "🏦 **【 كـشـف حـسـاب : الـخـزنـة الـمـلـكـيـة 】**\n"
            "━━━━━━━━━━━━━━\n"
            f"👤 **الـعـمـيـل:** `{u_name}`\n"
            f"🆔 **الـمـعـرف:** `{u_id}`\n"
            "━━━━━━━━━━━━━━\n"
            "💰 **الـرصـيـد الـنـقـدي:**\n"
            f"⮕ ` {u_data['balance']:,} ` ديـنـار\n"
            "────────────────\n"
            "🏅 **الأوسـمـة والـنـقـاط:**\n"
            f"💡 **الـثـقـافـة:** `{u_data.get('points', 0):,}` نـقـطـة\n"
            f"🖼️ **الـصـور:** `{u_data.get('image_points', 0):,}` نـقـطـة\n"
            f"🔥 **الـتـفـاعـل:** `{u_data.get('weekly_pts', 0):,}` نـقـطـة\n"
            "━━━━━━━━━━━━━━\n"
            "✨ *مـلاحـظـة: تـم تـحـديـث الـبـيـانات فـوراً*"
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
        
        # 👑 [1] درع الحماية الملكي: منع زرف المالك (أنس)
        if target.id == 5010882230:
            await update.message.reply_text("🚫 **عفواً يا حرامي:** حراس الامن يمنعونك من الاقتراب من خزنة انس! (تم تسجيل المحاولة)")
            return True

        t_data = db.get(User.id == target.id)
        
        if t_data and t_data.get('balance', 0) > 100000:
            amt = random.randint(10000, 100000)
            
            # حساب الأرصدة الجديدة للطرفين
            old_balance_u = u_data['balance']
            new_balance_u = old_balance_u + amt
            
            old_balance_t = t_data['balance']
            new_balance_t = old_balance_t - amt

            # تحديث قاعدة البيانات
            db.update({'balance': new_balance_u}, User.id == u_id)
            db.update({'balance': new_balance_t}, User.id == target.id)
            
            rob_msg = (
                "🥷 **【 كـشـف حـسـاب : سـحـب غـيـر مـصـرح 】**\n"
                "━━━━━━━━━━━━━━\n"
                "📜 **الـبـيـان:** عـمـلـيـة زرف احـتـرافـيـة\n"
                f"👤 **الـمُـنـفـذ:** `{u_name}`\n"
                f"👤 **الـضـحـيـة:** `{target.first_name}`\n"
                "────────────────\n"
                f"💰 **الـمـبـلـغ الـمـسـحوب:** `+{amt:,}` د\n"
                "────────────────\n"
                f"💳 **رصـيـدك الـحـالـي:** `{new_balance_u:,}` د\n"
                "━━━━━━━━━━━━━━\n"
                "⚠️ *تـنـبـيـه: تـم تـهريـب الأمـوال بـنـجـاح*"
            )
            await update.message.reply_text(rob_msg)
        else:
            # تم إصلاح علامات التنصيص وإضافة التنسيق الملكي
            await update.message.reply_text("❌ **فشل العملية:** الضحية مفلسة أو تحت حماية  أنس !")
        
        return True

        
