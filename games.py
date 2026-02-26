# games.py
import random

# هنا تضع الـ 100 سؤال لكل قسم (وضعت لك العينة ونظام الحذف يضمن عدم التكرار)
ALL_QUESTIONS = {
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة")] * 50, # مثال لـ 100 سؤال
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فلسطين؟", "القدس")] * 50,
    "اندية": [("الملكي؟", "ريال مدريد"), ("الزعيم؟", "الهلال")] * 50
}

used_questions = {}

async def get_game_data(game_type):
    if game_type not in ALL_QUESTIONS: return None, None
    
    if game_type not in used_questions or len(used_questions[game_type]) == len(ALL_QUESTIONS[game_type]):
        used_questions[game_type] = []
        
    available = [q for q in ALL_QUESTIONS[game_type] if q not in used_questions[game_type]]
    q, a = random.choice(available)
    used_questions[game_type].append((q, a))
    return q, a
