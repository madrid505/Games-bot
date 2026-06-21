import logging
import random
import asyncio
import os
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, PicklePersistence, ContextTypes
from config import BOT_TOKEN, OWNER_ID, GROUP_IDS
from handlers.games_handler import handle_messages, callback_handler
from telegram import Update
from royal_messages import GUESS_START_ANNOUNCEMENT
from hunter import hunter_handler

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- دالة التذكير الدوري (تُستدعى كل 15 ثانية) ---
async def send_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    hint = job.data 
    try:
        await context.bot.send_message(
            chat_id=job.chat_id,
            text=f"📢 **تذكير ملكي:**\n{hint}\n\nسارعوا بفك الرقم قبل فوات الأوان!",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"فشل إرسال التذكير الدوري: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر البداية خاصة عند الدخول من زر التخمين في الخاص"""
    u_id = update.effective_user.id

    if update.effective_chat.type == 'private':
        if context.args and context.args[0].startswith("guess_"):
            parts = context.args[0].split("_")
            target_chat_id = parts[1]
            allowed_admin_id = int(parts[2]) if len(parts) > 2 else None

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


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    await update.message.reply_text(
        f"🆔 **معلومات المعرف:**\n\n📌 آيدي المجموعة: `{chat_id}`\n👤 آيدي المستخدم: `{user_id}`"
    )


async def catch_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المعالج الرئيسي للرسائل"""

    if not update.message:
        return

    u_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""
    chat_id = str(update.effective_chat.id)

    # --- أولاً: معالجة المشرف في الخاص ---
    if update.effective_chat.type == 'private':
        target_chat_id = context.user_data.pop('awaiting_guess_for', None)

        if target_chat_id and text and text.isdigit():
            try:
                chat_id_to_send = int(target_chat_id)
            except ValueError:
                logging.error(f"خطأ: معرف المجموعة {target_chat_id} ليس رقماً صحيحاً")
                return

            logging.info(f"👑 تم إدخال رقم تخمين من الخاص للقروب: {chat_id_to_send}")

            context.bot_data[f"guess_ans_{chat_id_to_send}"] = str(text)

            secret_num = int(text)
            total_range = random.randint(45, 60)
            offset = random.randint(15, 30)
            lower_bound = max(1, secret_num - offset)
            upper_bound = lower_bound + total_range

            hint_content = f"الرقم بين: `{lower_bound}` و `{upper_bound}`"

            # 1. الرد في الخاص للمشرف
            await update.message.reply_text(
                f"✅ **تم الاعتماد!** الرقم السري هو ({text}). بدأ العد التنازلي في المجموعة."
            )

            # 2. إرسال رسالة التذكير الأولى
            try:
                await context.bot.send_message(
                    chat_id=chat_id_to_send,
                    text=GUESS_START_ANNOUNCEMENT.format(hint_content=hint_content),
                    parse_mode='Markdown'
                )
                
                # 3. جدولة التذكير كل 15 ثانية
                context.job_queue.run_repeating(
                    send_reminder_job, 
                    interval=15, 
                    first=15, 
                    chat_id=chat_id_to_send,
                    data=hint_content,
                    name=f"guess_{chat_id_to_send}"
                )
            except Exception as e:
                logging.error(f"فشل إرسال رسالة التخمين للمجموعة {chat_id_to_send}: {e}")
            
            return
            

    # --- ثانياً: فحص القروبات ---
    allowed_groups = [str(i).strip() for i in GROUP_IDS]
    
    if chat_id not in allowed_groups:
        return

    # --- تم تمرير الرسالة ---
    if update.message.text or update.message.photo:
        await handle_messages(update, context)


def main():
    # --- تنظيف حالة الـ persistence ---
    persistence_path = "/app/data/games_data/games_persistence"
    if os.path.exists(persistence_path):
        try:
            os.remove(persistence_path)
            print("👑 تم تنظيف ملف الـ persistence لضمان استقرار البوت!")
        except Exception as e:
            print(f"⚠️ تعذر حذف ملف الـ persistence: {e}")

    # استخدام المسار المرتبط بالـ Volume
    volume_path = "/app/data"
    games_dir = os.path.join(volume_path, "games_data")

    if not os.path.exists(games_dir):
        os.makedirs(games_dir)

    persistence = PicklePersistence(filepath=os.path.join(games_dir, "games_persistence"))

    app = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getid", get_id))
    app.add_handler(hunter_handler)

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), catch_ids))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("👑 إمبراطورية مونوبولي تعمل الآن مع نظام التخمين الدوري (15 ثانية)...")
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
