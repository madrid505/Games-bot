import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from config import BOT_TOKEN, OWNER_ID, GROUP_IDS
from handlers.games_handler import handle_messages, callback_handler
from telegram import Update
from telegram.ext import ContextTypes
# استيراد الرسائل الملكية
from royal_messages import GUESS_START_ANNOUNCEMENT

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر البداية خاصة عند الدخول من زر التخمين في الخاص"""
    u_id = update.effective_user.id
    
    # التأكد أن المستخدم في الخاص وليس في القروب
    if update.effective_chat.type == 'private':
        # التحقق إذا كان قادماً من زر "أضف تخمين"
        if context.args and context.args[0].startswith("guess_"):
            target_chat_id = context.args[0].replace("guess_", "")
            context.user_data['awaiting_guess_for'] = target_chat_id
            await update.message.reply_text(
                "🎯 **أهلاً بك يا سيادة المشرف في الخزنة الملكية**\n\n"
                "أرسل الآن الرقم السري الذي تريد من الأعضاء تخمينه:"
            )
            return
        
        await update.message.reply_text("👑 أهلاً بك في بوت إمبراطورية مونوبولي.")

async def catch_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المعالج الرئيسي للرسائل"""
    if not update.message: return
    
    u_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    # --- أولاً: معالجة المشرف في الخاص (استلام رقم التخمين) ---
    if update.effective_chat.type == 'private':
        target_chat_id = context.user_data.get('awaiting_guess_for')
        if target_chat_id and text:
            # تخزين الرقم في bot_data ليكون متاحاً لملف الألعاب
            context.bot_data[f"guess_ans_{target_chat_id}"] = text
            # مسح حالة الانتظار
            del context.user_data['awaiting_guess_for']
            
            await update.message.reply_text(f"✅ **تم اعتماد الرقم ({text}) بنجاح!**\nسيتمكن الأعضاء الآن من التخمين في المجموعة.")
            
            # إرسال إشعار للمجموعة بأن المسابقة بدأت باستخدام القالب الملكي
            try:
                await context.bot.send_message(
                    chat_id=target_chat_id, 
                    text=GUESS_START_ANNOUNCEMENT
                )
            except Exception as e:
                logging.error(f"Error sending announcement: {e}")
            return

    # --- ثانياً: تشغيل الأوامر الطبيعية في القروبات المسموحة ---
    if update.effective_chat.id in GROUP_IDS or u_id == OWNER_ID:
        # السماح بمعالجة النصوص والصور (لألعاب الصور)
        if update.message.text or update.message.photo:
            await handle_messages(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # معالجة أمر start (ضروري لنظام التخمين)
    app.add_handler(CommandHandler("start", start))
    
    # معالجة كافة الرسائل (نصوص وصور) مع استثناء الأوامر لعدم التداخل
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    
    # معالجة الأزرار (دفتر النتائج، الرصيد، ملوك التفاعل)
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 إمبراطورية مونوبولي تعمل الآن بنظام التخمين السري والداشبورد الملكي..")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
