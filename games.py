# games.py
import random

ALL_QUESTIONS = {
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة"), ("خاتم الأنبياء؟", "محمد")] * 34, 
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فرنسا؟", "باريس"), ("عاصمة فلسطين؟", "القدس")] * 34,
    "اندية": [("النادي الملكي؟", "ريال مدريد"), ("نادي القرن؟", "الاهلي"), ("البريميرليج في؟", "انجلترا")] * 34
}

used_questions = {k: [] for k in ALL_QUESTIONS.keys()}

async def get_game_data(game_key):
    if game_key not in ALL_QUESTIONS: return None, None
    if len(used_questions[game_key]) >= len(ALL_QUESTIONS[game_key]):
        used_questions[game_key] = []
    available = [q for q in ALL_QUESTIONS[game_key] if q not in used_questions[game_key]]
    if not available: return None, None
    q_pair = random.choice(available)
    used_questions[game_key].append(q_pair)
    return q_pair[0], q_pair[1]
