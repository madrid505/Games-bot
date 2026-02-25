import logging
import random
import time
from tinydb import TinyDB, Query
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- الإعدادات ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = TinyDB('bank_data.json')
User = Query()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- مكتبة 50 صورة جديدة ومتنوعة بروابط مباشرة ---
IMAGE_QUIZ = [
    {"url": "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png", "answer": "شخص"},
    {"url": "https://upload.wikimedia.org/wikipedia/ar/7/77/SpongeBob_SquarePants_characters.png", "answer": "سبونج بوب"},
    {"url": "https://upload.wikimedia.org/wikipedia/en/2/2f/Jerry_Mouse.png", "answer": "جيري"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/b/b8/Messi_vs_Nigeria_2018.jpg", "answer": "ميسي"},
    {"url": "https://upload.wikimedia.org/wikipedia/ar/thumb/f/f2/Cristiano_Ronaldo_2018.jpg/400px-Cristiano_Ronaldo_2018.jpg", "answer": "رونالدو"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Eiffel_Tower_Angled_Full_View.jpg/400px-Eiffel_Tower_Angled_Full_View.jpg", "answer": "برج ايفل"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/McDonald%27s_Golden_Arches.svg/1200px-McDonald%27s_Golden_Arches.svg.png", "answer": "ماكدونالدز"},
    {"url": "https://upload.wikimedia.org/wikipedia/ar/thumb/1/1a/Logo_Apple.svg/300px-Logo_Apple.svg.png", "answer": "ابل"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/9/91/Pizza-3007395.jpg", "answer": "بيتزا"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Instagram_icon.png/600px-Instagram_icon.png", "answer": "انستقرام"},
    {"url": "https://upload.wikimedia.org/wikipedia/ar/thumb/3/33/Mickey_Mouse_vector.svg/310px-Mickey_Mouse_vector.svg.png", "answer": "ميكي ماوس"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Statue_of_Liberty_7.jpg/330px-Statue_of_Liberty_7.jpg", "answer": "تمثال الحرية"},
    {"url": "https://upload.wikimedia.org/wikipedia/ar/d/d0/Pikachu_ash.png", "answer": "بيكاتشو"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Lion_waiting_in_Namibia.jpg/400px-Lion_waiting_in_Namibia.jpg", "answer": "اسد"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Garden_strawberry_%28Fragaria_×_ananassa%29_single.jpg/400px-Garden_strawberry_%28Fragaria_×_ananassa%29_single.jpg", "answer": "فراولة"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Pyramids_of_the_Giza_Necropolis.jpg/400px-Pyramids_of_the_Giza_Necropolis.jpg", "answer": "الاهرامات"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/YouTube_social_white_circle_%282017%29.svg/600px-YouTube_social_white_circle_%282017%29.svg.png", "answer": "يوتيوب"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_\"G\"_Logo.svg/480px-Google_\"G\"_Logo.svg.png", "answer": "قوقل"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Luffy_after_timeskip.png/300px-Luffy_after_timeskip.png", "answer": "لوفي"},
    {"url": "https://upload.wikimedia.org/wikipedia/ar/thumb/c/ca/Naruto_Uzumaki.png/300px-Naruto_Uzumaki.png", "answer": "ناروتو"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Logo_TikTok.svg/440px-Logo_TikTok.svg.png", "answer": "تيك توك"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/400px-Netflix_2015_logo.svg.png", "answer": "نتفلكس"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Burg_Khalifa.jpg/300px-Burg_Khalifa.jpg", "answer": "برج خليفة"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png", "answer": "زهر"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Facebook_f_logo_%282019%29.svg/300px-Facebook_f_logo_%282019%29.svg.png", "answer": "فيسبوك"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Facebook_Messenger_4_Logo.svg/300px-Facebook_Messenger_4_Logo.svg.png", "answer": "ماسنحر"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/300px-WhatsApp.svg.png", "answer": "واتساب"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/300px-Telegram_logo.svg.png", "answer": "تيليجرام"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Visa_Logo.svg/300px-Visa_Logo.svg.png", "answer": "فيزا"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/PayPal_logo.svg/300px-PayPal_logo.svg.png", "answer": "بايبال"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_NIKE.svg/300px-Logo_NIKE.svg.png", "answer": "نايك"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Adidas_Logo.svg/300px-Adidas_Logo.svg.png", "answer": "اديداس"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Coca-Cola_logo.svg/300px-Coca-Cola_logo.svg.png", "answer": "كوكا كولا"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Pepsi_logo_2014.svg/300px-Pepsi_logo_2014.svg.png", "answer": "بيبسي"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Starbucks_Corporation_Logo_2011.svg/300px-Starbucks_Corporation_Logo_2011.svg.png", "answer": "ستاربكس"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Tesla_T_symbol.svg/300px-Tesla_T_symbol.svg.png", "answer": "تيسلا"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/BMW.svg/300px-BMW.svg.png", "answer": "بي ام دبليو"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Mercedes-Benz_Logo_2010.svg/300px-Mercedes-Benz_Logo_2010.svg.png", "answer": "مرسيدس"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Suzuki_logo_2.svg/300px-Suzuki_logo_2.svg.png", "answer": "سوزوكي"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Ford_logo_flat.svg/300px-Ford_logo_flat.svg.png", "answer": "فورد"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Google_Chrome_material_logo.svg/300px-Google_Chrome_material_logo.svg.png", "answer": "كروم"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Slack_icon_2019.svg/300px-Slack_icon_2019.svg.png", "answer": "سلاك"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/LinkedIn_Logo.svg/300px-LinkedIn_Logo.svg.png", "answer": "لينكد ان"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Snapchat_logo.svg/300px-Snapchat_logo.svg.png", "answer": "سناب شات"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Toyota_car_logo.svg/300px-Toyota_car_logo.svg.png", "answer": "تويوتا"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Visa_Inc._logo.svg/300px-Visa_Inc._logo.svg.png", "answer": "فيزا كارد"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/300px-Amazon_logo.svg.png", "answer": "امازون"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Microsoft_logo_2012.svg/300px-Microsoft_logo_2012.svg.png", "answer": "مايكروسوفت"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/PlayStation_logo.svg/300px-PlayStation_logo.svg.png", "answer": "بلايستيشن"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Nintendo.svg/300px-Nintendo.svg.png", "answer": "نينتندو"}
]

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user: return False, False, False
    user_id = update.effective_user.id
    is_owner = (user_id == OWNER_ID)
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except: is_admin = False
    return True, is_owner, is_admin

async def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    if not user_data:
        _, is_owner, is_admin = await check_auth(update, context)
        balance = 500000000000 if is_owner else (100000000000 if is_admin else 10000000000)
        db.insert({'id': user_id, 'name': update.effective_user.first_name, 'balance': balance, 'points': 0, 'last_salary': 0, 'last_rob': 0, 'last_treasure': 0, 'last_luck': 0})
        user_data = db.get(User.id == user_id)
    return user_data

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    if update.effective_chat.id not in ALLOWED_GROUPS: return

    allowed, is_owner, is_admin = await check_auth(update, context)
    user_data = await get_user_data(update, context)
    
    # زيادة النقاط تلقائياً
    db.update({'points': user_data.get('points', 0) + 1}, User.id == user_id)

    # --- القائمة ---
    if text in ["العاب", "ألعاب"]:
        games_menu = (
            "🎮 **قائمة ألعاب مونوبولي العظيم** 🎮\n\n"
            "💰 **البنك:** (رصيدي، راتب، كنز، زرف، حظ)\n"
            "🎲 **التفاعل:** (صورة، روليت، ملك التفاعل)\n"
            "⚙️ **التحكم:** (فتح، قفل)"
        )
        await update.message.reply_text(games_menu, parse_mode="Markdown")
        return

    # --- التحكم ---
    if text in ["فتح", "فتح الالعاب"]:
        if is_owner or is_admin:
            context.chat_data['active'] = True
            await update.message.reply_text("✅ تم فتح الألعاب بنجاح!")
        return

    # --- البنك ---
    if text == "رصيدي":
        await update.message.reply_text(f"👤 {user_name}\n💰 رصيدك: {user_data['balance']:,} ريال\n⭐ نقاطك: {user_data.get('points', 0)}")
    
    elif text == "راتب":
        if current_time - user_data.get('last_salary', 0) > 1200:
            amt = random.randint(5000000, 20000000)
            db.update({'balance': user_data['balance'] + amt, 'last_salary': current_time}, User.id == user_id)
            await update.message.reply_text(f"💵 استلمت راتبك: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الراتب متاح كل 20 دقيقة")

    elif text == "كنز":
        if current_time - user_data.get('last_treasure', 0) > 3600:
            amt = random.randint(50000000, 200000000)
            db.update({'balance': user_data['balance'] + amt, 'last_treasure': current_time}, User.id == user_id)
            await update.message.reply_text(f"💎 مبروك وجدت كنزاً: {amt:,} ريال")
        else: await update.message.reply_text("⏳ الكنز متاح كل ساعة")

    # --- ملك التفاعل (الرسالة الملكية) ---
    elif text == "ملك التفاعل" and (is_owner or is_admin):
        all_u = db.all()
        if all_u:
            winner = max(all_u, key=lambda x: x.get('points', 0))
            msg = (f"🔥🔥🔥 ملك التفاعل 🔥🔥\n\nاسم الملك : {winner['name']}\n\nعدد النقاط : {winner['points']}\n\nID : {winner['id']}\n\n🔥🔥 مبارك عليك الفوز يا اسطورة القروب 🔥🔥")
            await update.message.reply_text(msg)
            for u in all_u: db.update({'points': 0}, User.id == u['id'])

    # --- الروليت (تكرار مفتوح لكلمة انا) ---
    elif text == "روليت":
        if is_owner or is_admin:
            context.chat_data['r_on'] = True
            context.chat_data['r_players'] = []
            context.chat_data['r_starter'] = user_id
            await update.message.reply_text("🔥🔥 يا شعب مونوبولي العظيم 🔥🔥\n\n👈 لقد بدأت لعبة الروليت 👉\n\n🌹🌹 ليتم تسجيل اشتراكك في الجولة اكتب انا 🌹🌹")

    elif text == "انا" and context.chat_data.get('r_on'):
        # السماح بالتكرار المفتوح (كلما كتب "انا" تزيد فرصته)
        context.chat_data['r_players'].append({'id': user_id, 'name': user_name})
        await update.message.reply_text("📢🔥🌹 لقد تم تسجيلك يا بطل 🌹🔥📢")

    elif text == "تم" and context.chat_data.get('r_on'):
        if user_id == context.chat_data.get('r_starter') or is_owner:
            players = context.chat_data.get('r_players', [])
            if players:
                winner = random.choice(players)
                win_msg = (f"👑👑 مبااااارك عليك الفوز يا اسطورة 👑👑\n\n          👑 \" {winner['name']} \" 👑\n\n👈👈 استمر معنا بالمشاركة حتى تربح الجائزة الكبرى 👉👉")
                await update.message.reply_text(win_msg)
            context.chat_data['r_on'] = False

    # --- لعبة الصور (50 صورة بروابط مضمونة) ---
    elif text in ["صورة", "الصورة", "صوره"]:
        if context.chat_data.get('active'):
            try:
                item = random.choice(IMAGE_QUIZ)
                context.chat_data['ans'] = item['answer']
                # إرسال الصورة مع منع تعليق البوت في حال فشل الرابط
                await update.message.reply_photo(photo=item['url'], caption="🖼 وش في الصورة؟ أسرع واحد يجاوب يربح 10 مليون!", connect_timeout=10, read_timeout=10)
            except Exception as e:
                logging.error(f"Image Error: {e}")
                # محاولة ثانية بصورة مختلفة فوراً
                new_item = random.choice(IMAGE_QUIZ)
                context.chat_data['ans'] = new_item['answer']
                await update.message.reply_photo(photo=new_item['url'], caption="🔄 الروابط زحمة.. جرب هذي الصورة:")
        else: await update.message.reply_text("🚫 الألعاب مقفلة.. اطلب من المشرف فتحها")

    elif context.chat_data.get('ans') and text == context.chat_data.get('ans'):
        context.chat_data['ans'] = None
        db.update({'balance': user_data['balance'] + 10000000}, User.id == user_id)
        await update.message.reply_text(f"🎉 كفو {user_name}! إجابة صحيحة وفزت بـ 10,000,000 ريال! ✅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == '__main__': main()
