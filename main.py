import logging
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- الإعدادات (محفوظة كما طلبت) ---
BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- نظام الحماية ---
async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat: return False, False, False
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if update.effective_chat.type in ["group", "supergroup"]:
        if chat_id not in ALLOWED_GROUPS:
            await update.message.reply_text("❌ البوت غير مسموح له بالعمل هنا.")
            await context.bot.leave_chat(chat_id)
            return False, False, False

    is_owner = (user_id == OWNER_ID)
    member = await context.bot.get_chat_member(chat_id, user_id)
    is_admin = member.status in ['administrator', 'creator']
    return True, is_owner, is_admin

# --- منطق الألعاب ---

# 1. لعبة الرد السريع
async def fast_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auth, _, _ = await check_auth(update, context)
    if not auth: return
    
    words = ["تفاحة", "سيف", "قلم", "كمبيوتر", "مملكة", "تلجرام", "سرعة"]
    target_word = random.choice(words)
    context.chat_data['game_active'] = True
    context.chat_data['target'] = target_word
    
    await update.message.reply_text(f"🚀 أسرع واحد يكتب الكلمة التالية يربح:\n\n`{target_word}`", parse_mode='MarkdownV2')

# 2. لعبة تخمين الرقم
async def guess_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auth, _, _ = await check_auth(update, context)
    if not auth: return
    
    number = random.randint(1, 10)
    context.chat_data['guess_active'] = True
    context.chat_data['number'] = number
    await update.message.reply_text("🔢 خمنت رقماً من 1 إلى 10، من سيعرفه أولاً؟")

# --- مراقب الرسائل (لمعرفة الفائز) ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    # التحقق من لعبة الرد السريع
    if context.chat_data.get('game_active'):
        if update.message.text == context.chat_data.get('target'):
            context.chat_data['game_active'] = False
            await update.message.reply_text(f"🎉 كفو! {update.effective_user.mention_html()} هو الأسرع!", parse_mode='HTML')

    # التحقق من لعبة التخمين
    if context.chat_data.get('guess_active'):
        if update.message.text.isdigit() and int(update.message.text) == context.chat_data.get('number'):
            context.chat_data['guess_active'] = False
            await update.message.reply_text(f"🎯 صح! {update.effective_user.mention_html()} جاب الرقم صح!", parse_mode='HTML')

# --- أوامر الإدارة ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auth, is_owner, is_admin = await check_auth(update, context)
    if not auth: return
    
    msg = "🎮 **بوت الألعاب جاهز!**\n\n"
    msg += "🕹 **الأوامر المتوفرة:**\n"
    msg += "/fast - لعبة الرد السريع\n"
    msg += "/guess - لعبة تخمين الأرقام\n\n"
    if is_owner or is_admin:
        msg += "⚡️ أنت تملك صلاحيات إدارية."
    
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fast", fast_click))
    app.add_handler(CommandHandler("guess", guess_number))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
