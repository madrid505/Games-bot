import logging
import random
import asyncio
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
    if update.effective_chat.type == 'private':
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
            context.bot_data[f"guess_ans_{target_chat_id}"] = text
            
            # 🛡️ حساب المدى التقريبي (20-30 عدد) مع البرواز الملكي
            hint_box = ""
            try:
                secret_num = int(text)
                total_range = random.randint(20, 30)
                offset = random.randint(5, total_range - 5)
                lower_bound = max(1, secret_num - offset)
                upper_bound = lower_bound + total_range
                
                hint_box = (
                    f"\n\n┏━━━━━━━ 👑 ━━━━━━━┓\n"
                    f"     ✨ **تلميح الخزنة الملكية** ✨\n"
                    f"     الرقم بين: `{lower_bound}` و `{upper_bound}`\n"
                    f"┗━━━━━━━ 👑 ━━━━━━━┛"
                )
            except ValueError: pass

            del context.user_data['awaiting_guess_for']
            await update.message.reply_text(f"✅ **تم الاعتماد بنجاح!** بدأ العد التنازلي الآن في المجموعة.")
            
            # --- ⏳ نظام العد التنازلي الحماسي مع التنبيهات ---
            try:
                countdown_msg = await context.bot.send_message(chat_id=target_chat_id, text="⚠️ **تأهبوا.. سيبدأ التخمين بعد:**\n🔥 **3**")
                await asyncio.sleep(1.2)
                await countdown_msg.edit_text("⚠️ **تأهبوا.. سيبدأ التخمين بعد:**\n🔥 **2**")
                await asyncio.sleep(1.2)
                await countdown_msg.edit_text("⚠️ **تأهبوا.. سيبدأ التخمين بعد:**\n💣 **1** 📢")
                await asyncio.sleep(1)
                
                # إرسال إشعار البداية النهائي مع التلميح المزخرف
                await countdown_msg.edit_text(f"{GUESS_START_ANNOUNCEMENT}{hint_box}")
            except Exception as e:
                logging.error(f"Error in countdown: {e}")
            return

    # --- ثانياً: تشغيل الأوامر الطبيعية في القروبات المسموحة ---
    if update.effective_chat.id in GROUP_IDS or u_id == OWNER_ID:
        if update.message.text or update.message.photo:
            await handle_messages(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("👑 إمبراطورية مونوبولي تعمل الآن بالنظام المطور (عد تنازلي + تلميحات)..")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
