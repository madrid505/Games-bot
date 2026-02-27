import random
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_data, db, User
from config import GROUP_IDS

# قاعدة بيانات الصور (File IDs اللي استخرجناها من صورك)
# ملاحظة: استبدل 'FILE_ID_...' بالأكواد الفعلية التي تظهر في سجلات البوت عند استلام الصور
IMAGE_QUIZ = [
    {"file_id": "FILE_ID_JAMAL", "answer": "جمل"},
    {"file_id": "FILE_ID_SOMAL", "answer": "صومال"},
    {"file_id": "FILE_ID_THUBAB", "answer": "ذباب"},
    {"file_id": "FILE_ID_LIGHT", "answer": "العلم نور"},
    {"file_id": "FILE_ID_GOLD", "answer": "سكوتك من ذهب"}
]

async def start_image_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة لبدء لعبة الصور عشوائياً"""
    if update.effective_chat.id not in GROUP_IDS:
        return

    # اختيار صورة عشوائية
    quiz = random.choice(IMAGE_QUIZ)
    context.chat_data['img_ans'] = quiz['answer']
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=quiz['file_id'],
        caption="🎮 **لعبة الصور الملكية**\n\nماذا تعني هذه الصورة؟"
    )

async def check_image_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, u_data: dict):
    """فحص الإجابة وتحديث النقاط فقط"""
    correct_ans = context.chat_data.get('img_ans')
    
    if correct_ans and text == correct_ans:
        u_id = update.effective_user.id
        u_name = update.effective_user.first_name
        
        # تحديث النقاط (+1) فقط بدون لمس الرصيد (Balance)
        new_points = u_data.get('points', 0) + 1
        db.update({'points': new_points}, User.id == u_id)
        
        await update.message.reply_text(
            f"✅ **إجابة عبقرية يا {u_name}!**\n\nلقد حصلت على **نقطة واحدة** في سجل ملوك التفاعل. 🏆"
        )
        
        # مسح الإجابة لمنع التكرار
        context.chat_data['img_ans'] = None
        return True
    return False
