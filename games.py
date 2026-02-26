# games.py
import random

# مصفوفة ضخمة (يجب تعبئتها بـ 100 سؤال حقيقي، هنا وضعت لك القالب الجاهز)
ALL_QUESTIONS = {
    "دين": [("أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة"), ("خاتم الأنبياء؟", "محمد")] * 34, # مكررة تقنياً لتصل لـ 100، استبدلها بأسئلة فريدة
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فرنسا؟", "باريس"), ("عاصمة فلسطين؟", "القدس")] * 34,
    "اندية": [("الملكي؟", "ريال مدريد"), ("نادي القرن؟", "الاهلي"), ("البريميرليج في؟", "انجلترا")] * 34
}

# ذاكرة الأسئلة المستخدمة لمنع التكرار
used_questions = {k: [] for k in ALL_QUESTIONS.keys()}

async def get_game_data(game_type):
    if game_type not in ALL_QUESTIONS: return None, None
    
    # إذا خلصت الأسئلة، صفر الذاكرة وابدأ من جديد
    if len(used_questions[game_type]) >= len(ALL_QUESTIONS[game_type]):
        used_questions[game_type] = []
        
    available = [q for q in ALL_QUESTIONS[game_type] if q not in used_questions[game_type]]
    if not available: 
        used_questions[game_type] = []
        available = ALL_QUESTIONS[game_type]
        
    q, a = random.choice(available)
    used_questions[game_type].append((q, a))
    return q, a
