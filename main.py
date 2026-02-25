import logging
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- الإعدادات الخاصة بك ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- نظام الحماية والتحقق ---
async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user: return False, False, False
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # التحقق من المجموعة
    if update.effective_chat.type in ["group", "supergroup"]:
        if chat_id not in ALLOWED_GROUPS:
            await update.message.reply_text("❌ البوت غير مسموح له بالعمل هنا.")
            await context.bot.leave_chat(chat_id)
            return False, False, False

    # التحقق من الرتب
    is_owner = (user_id == OWNER_ID)
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except:
        is_admin = False
        
    return True, is_owner, is_admin

# --- معالج الرسائل الرئيسي (الأوامر بدون رموز + منطق الألعاب) ---
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    allowed, is_owner, is_admin = await check_auth(update, context)
    if not allowed: return

    # 1. أوامر الإدارة (بدون رموز)
    if text == "فتح":
        if is_owner or is_admin:
            context.chat_data['status'] = 'open'
            await update.message.reply_text("✅ تم فتح الألعاب بنجاح!")
        else:
            await update.message.reply_text("⚠️ هذا الأمر للمدراء فقط.")
        return

    if text == "قفل":
        if is_owner or is_admin:
            context.chat_data['status'] = 'closed'
            await update.message.reply_text("🔒 تم قفل الألعاب.")
        else:
            await update.message.reply_text("⚠️ هذا الأمر للمدراء فقط.")
        return

    # 2. أوامر الألعاب (بدون رموز)
    if text == "لعبة":
        if context.chat_data.get('status') != 'open':
            await update.message.reply_text("🚫 الألعاب مقفلة حالياً.")
            return
        words = ["مملكة", "صقر", "برمجة", "تلجرام", "سيارة", "أسد", "لعبة", "تفاحة", "سماء"]
        target = random.choice(words)
        context.chat_data['game_type'] = 'fast'
        context.chat_data['target'] = target
        await update.message.reply_text(f"🚀 أسرع واحد يكتب الكلمة:\n\n`{target}`", parse_mode='MarkdownV2')
        return

    if text == "تخمين":
        if context.chat_data.get('status') != 'open':
            await update.message.reply_text("🚫 الألعاب مقفلة حالياً.")
            return
        number = random.randint(1, 10)
        context.chat_data['game_type'] = 'guess'
        context.chat_data['target'] = str(number)
        await update.message.reply_text("🔢 خمنت رقم من 1 إلى 10، مين يعرفه؟")
        return

    # 3. التحقق من الإجابات للفوز
    game_type = context.chat_data.get('game_type')
    target = context.chat_data.get('target')
    
    if game_type and text == target:
        context.chat_data['game_type'] = None  # إنهاء اللعبة الحالية
        await update.message.reply_text(f"🎉 كفو {update.effective_user.mention_html()}! إجابتك صحيحة ✅", parse_mode='HTML')

# --- أمر البداية للمساعدة ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed, _, _ = await check_auth(update, context)
    if not allowed: return
    
    help_text = (
        "🎮 **بوت الألعاب (بدون رموز)**\n\n"
        "🕹 **الكلمات المتاحة:**\n"
        "• `لعبة` - لبدء تحدي الكلمات\n"
        "• `تخمين` - لبدء تحدي الأرقام\n\n"
        "🛠 **للإدارة فقط:**\n"
        "• `فتح` - لفتح اللعب\n"
        "• `قفل` - لمنع اللعب"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # استقبال كل الرسائل ومعالجتها كأوامر أو إجابات
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    print("🚀 البوت يعمل بالكلمات المباشرة وبدون رموز...")
    app.run_polling()

if __name__ == '__main__':
    main()
