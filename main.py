import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- الإعدادات الخاصة بك التي زودتني بها ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# إعداد السجلات لمراقبة أداء البوت على Northflank
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# --- دالة التحقق من الصلاحيات والمجموعات ---
async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user:
        return False, False, False

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 1. التحقق: هل المجموعة مسموح لها؟ (للمجموعات فقط)
    if update.effective_chat.type in ["group", "supergroup"]:
        if chat_id not in ALLOWED_GROUPS:
            await update.message.reply_text("❌ عذراً، هذا البوت خاص ولا يعمل في هذه المجموعة. سيغادر الآن.")
            await context.bot.leave_chat(chat_id)
            return False, False, False

    # 2. التحقق من الرتب داخل المجموعة المسموحة
    is_owner = (user_id == OWNER_ID)
    is_admin = False
    
    if not is_owner:
        member = await context.bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    
    return True, is_owner, is_admin

# --- الأوامر ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_allowed, is_owner, is_admin = await check_auth(update, context)
    if not is_allowed: return

    welcome_msg = "🎮 أهلاً بك في بوت الألعاب الخاص!\n\n"
    if is_owner:
        welcome_msg += "👑 رتبتك: المالك (لديك كامل الصلاحيات)"
    elif is_admin:
        welcome_msg += "🛡️ رتبتك: مدير/مشرف (يمكنك إدارة الألعاب)"
    else:
        welcome_msg += "👤 رتبتك: لاعب"
        
    await update.message.reply_text(welcome_msg)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_allowed, _, _ = await check_auth(update, context)
    if not is_allowed: return
    
    await update.message.reply_text("🎲 بدأت اللعبة! (يمكنك إضافة منطق ألعابك هنا)")

# --- تشغيل البوت ---
def main():
    # بناء التطبيق باستخدام التوكن الخاص بك
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة الأوامر للبوت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    print("🚀 البوت يعمل الآن ومحمي للمجموعات المحددة فقط...")
    app.run_polling()

if __name__ == '__main__':
    main()
