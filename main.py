import logging
import random
import asyncio
import os  # إضافة مكتبة النظام
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, PicklePersistence # إضافة Persistence
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
        # تم تحديث الرابط ليدعم استخراج ID المجموعة و ID المشرف
        if context.args and context.args[0].startswith("guess_"):
            parts = context.args[0].split("_")
            target_chat_id = parts[1]
            allowed_admin_id = int(parts[2]) if len(parts) > 2 else None

            # حماية: التأكد أن من يضغط على الرابط هو نفس المشرف الذي أطلقه
            if allowed_admin_id and u_id != allowed_admin_id:
                await update.message.reply_text("⚠️ **عفواً:** هذا الزر مخصص للمشرف الذي أطلقه فقط!")
                return

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
        if target_chat_id and text and text.isdigit():
            context.bot_data[f"guess_ans_{target_chat_id}"] = text
            
            # 🛡️ [تعديل] حساب المدى الديناميكي (بناءً على طلبك 1-60)
            secret_num = int(text)
            total_range = random.randint(45, 60) # المدى الكلي بين 45 و 60 رقم
            offset = random.randint(15, 30) # الإزاحة لليسار
            lower_bound = max(1, secret_num - offset)
            upper_bound = lower_bound + total_range
            
            hint_content = f"الرقم بين: `{lower_bound}` و `{upper_bound}`"
            hint_box = (
                f"\n\n┏━━━━━━━ 👑 ━━━━━━━┓\n"
                f"     ✨ **تلميح الخزنة الملكية** ✨\n"
                f"     {hint_content}\n"
                f"┗━━━━━━━ 👑 ━━━━━━━┛"
            )

            del context.user_data['awaiting_guess_for']
            await update.message.reply_text(f"✅ **تم الاعتماد!** الرقم السري هو ({text}). بدأ العد التنازلي في المجموعة.")
            
            # --- ⏳ [تعديل] نظام العد التنازلي + مهمة التذكير التلقائي كل 10 ثوانٍ ---
            try:
                countdown_msg = await context.bot.send_message(chat_id=target_chat_id, text="⚠️ **تأهبوا.. سيبدأ التخمين بعد:**\n🔥 **3**")
                await asyncio.sleep(1.2)
                await countdown_msg.edit_text("⚠️ **تأهبوا.. سيبدأ التخمين بعد:**\n🔥 **2**")
                await asyncio.sleep(1.2)
                await countdown_msg.edit_text("⚠️ **تأهبوا.. سيبدأ التخمين بعد:**\n💣 **1** 📢")
                await asyncio.sleep(1)
                await countdown_msg.edit_text(f"{GUESS_START_ANNOUNCEMENT}{hint_box}")

                # 🔄 تشغيل حلقة التذكير التلقائي في الخلفية
                async def reminder_loop():
                    # تستمر الحلقة طالما أن الرقم لم يتم تخمينه (موجود في bot_data)
                    while context.bot_data.get(f"guess_ans_{target_chat_id}") == text:
                        await asyncio.sleep(10) # انتظر 10 ثوانٍ
                        if context.bot_data.get(f"guess_ans_{target_chat_id}") == text:
                            try:
                                await context.bot.send_message(
                                    target_chat_id, 
                                    f"📢 **تذكير اداري:**\n🎯 لا زال التخمين مستمراً!\n\n👑 {hint_content}"
                                )
                            except: break
                
                asyncio.create_task(reminder_loop())

            except Exception as e:
                logging.error(f"Error in countdown or reminder: {e}")
            return

    # --- ثانياً: تشغيل الأوامر الطبيعية في القروبات المسموحة ---
    if update.effective_chat.id in [int(i) for i in GROUP_IDS] or u_id == OWNER_ID:
        if update.message.text or update.message.photo:
            await handle_messages(update, context)

def main():
    # --- إعداد مسار الحفظ لضمان عدم التداخل ---
    volume_path = "/app/data"
    games_dir = os.path.join(volume_path, "games_data")
    if not os.path.exists(games_dir):
        os.makedirs(games_dir)
    
    # تفعيل نظام الحفظ الدائم
    persistence = PicklePersistence(filepath=os.path.join(games_dir, "games_persistence"))

    app = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("👑 إمبراطورية مونوبولي تعمل الآن بالنظام المطور (تذكير كل 10ث + مدى 60 رقم + حفظ دائم)..")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
