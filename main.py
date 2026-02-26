‏import logging
‏import random
‏import time
‏import json
‏import os
‏from tinydb import TinyDB, Query
‏from telegram import Update
‏from telegram.ext import Application, ContextTypes, MessageHandler, filters
‏
‏# --- الإعدادات ---
‏BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
‏OWNER_ID = 5010882230
‏ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
‏
‏db = TinyDB('bank_data.json')
‏User = Query()
‏
‏logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
‏
‏# --- بيانات الألعاب الجديدة ---
‏GAMES_DATA = {
‏    "اسئله": [("ما هي عاصمة السعودية؟", "الرياض"), ("من هو خاتم الأنبياء؟", "محمد"), ("كم عدد قارات العالم؟", "7")],
‏    "ترتيب": [("ي س م ي", "ميسي"), ("ر و ن ا ل د و", "رونالدو"), ("ت ف ا ح", "تفاح")],
‏    "تفكيك": [("مدرسة", "م د ر س ة"), ("كتاب", "ك ت ا ب"), ("سيارة", "س ي ا ر ة")],
‏    "عكس الكلمة": [("قمر", "رمق"), ("شمس", "سمش"), ("ورد", "درو")],
‏    "حزوره": [("ما هو الشيء الذي يكتب ولا يقرأ؟", "القلم"), ("له أسنان ولا يعض؟", "المشط")],
‏    "عواصم": [("مصر", "القاهرة"), ("الأردن", "عمان"), ("سوريا", "دمشق"), ("العراق", "بغداد")],
‏    "معاني": [("🍎", "تفاح"), ("🚗", "سيارة"), ("⚽", "كرة"), ("🏠", "بيت")],
‏}
‏
‏async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
‏    user_id = update.effective_user.id
‏    user_name = update.effective_user.first_name
‏    user_data = db.get(User.id == user_id)
‏    
‏    if not user_data:
‏        # تحديد الرصيد حسب الرتبة (للمرة الأولى فقط)
‏        is_owner = (user_id == OWNER_ID)
‏        try:
‏            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
‏            is_admin = member.status in ['administrator', 'creator']
‏        except: is_admin = False
‏        
‏        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
‏        user_data = {
‏            'id': user_id, 'name': user_name, 'balance': balance, 
‏            'points': 0, 'roulette_wins': 0, 'stolen_total': 0,
‏            'last_salary': 0, 'last_rob': 0, 'last_treasure': 0, 'last_luck': 0
‏        }
‏        db.insert(user_data)
‏    return user_data
‏
‏async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
‏    if not update.message or not update.message.text: return
‏    text = update.message.text.strip()
‏    parts = text.split()
‏    cmd = parts[0]
‏    user_id = update.effective_user.id
‏    user_name = update.effective_user.first_name
‏    chat_id = update.effective_chat.id
‏    
‏    if chat_id not in ALLOWED_GROUPS: return
‏    
‏    # جلب بيانات المستخدم (مصلحة لضمان عدم التصفير)
‏    u_data = await get_user_data(update, context)
‏    
‏    # تحديث اسم المستخدم والنقاط التفاعلية
‏    db.update({'points': u_data.get('points', 0) + 1, 'name': user_name}, User.id == user_id)
‏
‏    # --- [1] أوامر البنك (الإصلاح الشامل) ---
‏    if cmd == "رصيدي":
‏        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {u_data['balance']:,} ريال")
‏
‏    elif cmd == "راتب":
‏        if time.time() - u_data.get('last_salary', 0) > 600:
‏            amt = random.randint(5000000, 15000000)
‏            db.update({'balance': u_data['balance'] + amt, 'last_salary': time.time()}, User.id == user_id)
‏            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} ريال")
‏        else: await update.message.reply_text("⏳ الراتب متاح كل 10 دقائق")
‏
‏    elif cmd == "زرف":
‏        if time.time() - u_data.get('last_rob', 0) > 300:
‏            others = [u for u in db.all() if u['id'] != user_id and u['balance'] > 1000000]
‏            if others:
‏                target = random.choice(others)
‏                amt = random.randint(100000, 5000000)
‏                db.update({'balance': u_data['balance'] + amt, 'last_rob': time.time(), 'stolen_total': u_data.get('stolen_total', 0) + amt}, User.id == user_id)
‏                db.update({'balance': target['balance'] - amt}, User.id == target['id'])
‏                await update.message.reply_text(f"🥷 زرفت {amt:,} ريال من {target['name']}")
‏        else: await update.message.reply_text("⏳ الزرف كل 5 دقائق")
‏
‏    elif cmd == "كنز":
‏        if time.time() - u_data.get('last_treasure', 0) > 3600:
‏            amt = random.randint(50000000, 100000000)
‏            db.update({'balance': u_data['balance'] + amt, 'last_treasure': time.time()}, User.id == user_id)
‏            await update.message.reply_text(f"💎 كفو! لقيت كنز فيه {amt:,} ريال")
‏        else: await update.message.reply_text("⏳ الكنز متاح كل ساعة")
‏
‏    elif cmd == "هدية" and len(parts) > 1 and update.message.reply_to_message:
‏        try:
‏            amt = int(parts[1])
‏            target_id = update.message.reply_to_message.from_user.id
‏            if u_data['balance'] >= amt > 0:
‏                db.update({'balance': u_data['balance'] - amt}, User.id == user_id)
‏                t_data = db.get(User.id == target_id)
‏                db.update({'balance': t_data['balance'] + amt}, User.id == target_id)
‏                await update.message.reply_text(f"🎁 تم إرسال {amt:,} ريال هدية إلى {t_data['name']}")
‏        except: pass
‏
‏    # --- [2] ألعاب التحدي (النظام الجديد) ---
‏    if cmd in GAMES_DATA:
‏        q, a = random.choice(GAMES_DATA[cmd])
‏        context.chat_data['game_ans'] = a
‏        await update.message.reply_text(f"🎮 لعبة {cmd}:\n\nالسؤال: 【 {q} 】\n\n(أسرع واحد يجاوب يربح 5 مليون)")
‏        return
‏
‏    if context.chat_data.get('game_ans') and text == context.chat_data.get('game_ans'):
‏        context.chat_data['game_ans'] = None
‏        db.update({'balance': u_data['balance'] + 5000000}, User.id == user_id)
‏        await update.message.reply_text(f"✅ كفو {user_name}! إجابتك صح وفزت بـ 5,000,000 ريال!")
‏
‏    # --- [3] ألعاب الحظ السريع ---
‏    if cmd == "نرد":
‏        await update.message.reply_dice(emoji="🎲")
‏    elif cmd == "سله" or cmd == "سلة":
‏        await update.message.reply_dice(emoji="🏀")
‏    elif cmd == "كوره" or cmd == "كرة":
‏        await update.message.reply_dice(emoji="⚽")
‏    elif cmd == "بولينق":
‏        await update.message.reply_dice(emoji="🎳")
‏    elif cmd == "سهم":
‏        await update.message.reply_dice(emoji="🎯")
‏
‏    # --- [4] الروليت الملكي (المحفوظ) ---
‏    elif text == "روليت":
‏        context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], user_id
‏        await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")
‏
‏    elif text == "انا" and context.chat_data.get('r_on'):
‏        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
‏        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")
‏
‏    elif text == "تم" and context.chat_data.get('r_on'):
‏        if user_id == context.chat_data.get('r_starter') or user_id == OWNER_ID:
‏            players = context.chat_data.get('r_players', [])
‏            if players:
‏                winner = random.choice(players)
‏                w_db = db.get(User.id == winner['id'])
‏                new_w = w_db.get('roulette_wins', 0) + 1
‏                db.update({'roulette_wins': new_w}, User.id == winner['id'])
‏                await update.message.reply_text(f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {winner['name']} \" 👑\n\n🏆 فوزك رقم: ( {new_w} )")
‏                if new_w >= 5:
‏                    await update.message.reply_text(f"👑👑👑 ملك الروليت 👑👑👑\n\n             👑 \" {winner['name']} \" 👑\n\n       🔥🔥 \"{new_w} نقاط\"🔥🔥")
‏                    for u in db.all(): db.update({'roulette_wins': 0}, User.id == u['id'])
‏            context.chat_data['r_on'] = False
‏
‏    # --- [5] ملك التفاعل و التوب ---
‏    elif text == "توب الروليت":
‏        top = sorted(db.all(), key=lambda x: x.get('roulette_wins', 0), reverse=True)[:10]
‏        msg = "🏆 **قائمة أساطير الروليت:**\n\n"
‏        icons = ["👑", "🔥", "♥️"]
‏        for i, u in enumerate(top):
‏            if u.get('roulette_wins', 0) > 0:
‏                icon = icons[i] if i < 3 else f"{i+1}-"
‏                msg += f"{icon} \" {u['name']} \" + ( {u['roulette_wins']} )\n"
‏        await update.message.reply_text(msg)
‏
‏    elif text == "ملك التفاعل":
‏        winner = max(db.all(), key=lambda x: x.get('points', 0))
‏        await update.message.reply_text(f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {winner['name']}\n\nعدد النقاط : {winner['points']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة 🔥🔥")
‏
‏    elif text == "العاب":
‏        await update.message.reply_text("🎮 **قائمة الألعاب المتاحة:**\n\n💰 **البنك:** (رصيدي، راتب، زرف، كنز، هدية)\n🧩 **تحدي:** (اسئله، ترتيب، تفكيك، عكس الكلمة، حزوره، عواصم، معاني)\n🎲 **سرعة:** (نرد، سله، كوره، بولينق، سهم)\n👑 **الملكية:** (روليت، توب الروليت، ملك التفاعل)")
‏
‏def main():
‏    app = Application.builder().token(BOT_TOKEN).build()
‏    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
‏    app.run_polling()
‏
‏if __name__ == '__main__': main()
‏
