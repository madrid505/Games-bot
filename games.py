# games.py
import random

ALL_QUESTIONS = {
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة"), ("سورة تعدل ثلث القرآن؟", "الإخلاص")] * 34,
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فلسطين؟", "القدس"), ("عاصمة فرنسا؟", "باريس")] * 34,
    "اندية": [("النادي الملكي؟", "ريال مدريد"), ("نادي القرن؟", "الاهلي"), ("نادي النصر؟", "العالمي")] * 34,
    "أعلام": [("علم لونه أحمر وأبيض وفيه نجمة وخلال؟", "تونس"), ("علم لونه أخضر فيه سيف؟", "السعودية")] * 50
}

used_questions = {k: [] for k in ALL_QUESTIONS.keys()}

async def get_game_data(key, is_lucky_hour=False):
    # مسابقات الحظ (تعمل مراهنة إلا لو ساعة الحظ مفعلة)
    if key in ["حرب العصابات", "القنبلة", "المزاد"]:
        win = random.random() > (0.3 if is_lucky_hour else 0.5) # نسبة فوز أكبر في ساعة الحظ
        amt = random.randint(10000000, 50000000) if is_lucky_hour else random.randint(5000000, 20000000)
        return ("WIN" if win else "LOSE"), amt
    
    if key == "صيد":
        code = str(random.randint(1000, 9999))
        return f"🎯 أسرع واحد يكتب الرقم: `{code}`", code

    if key in ALL_QUESTIONS:
        if len(used_questions[key]) >= len(ALL_QUESTIONS[key]): used_questions[key] = []
        available = [q for q in ALL_QUESTIONS[key] if q not in used_questions[key]]
        q_pair = random.choice(available)
        used_questions[key].append(q_pair)
        return q_pair[0], q_pair[1]
    return None, None
