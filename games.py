# games.py
import random

# ملاحظة: يمكنك زيادة هذه القوائم إلى 100 سؤال بسهولة بنفس التنسيق
ALL_QUESTIONS = {
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة"), ("سورة تعدل ثلث القرآن؟", "الإخلاص")] * 34,
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فلسطين؟", "القدس"), ("عاصمة مصر؟", "القاهرة")] * 34,
    "اندية": [("النادي الملكي؟", "ريال مدريد"), ("نادي القرن؟", "الاهلي"), ("نادي النصر؟", "العالمي")] * 34
}

used_questions = {k: [] for k in ALL_QUESTIONS.keys()}

async def get_game_data(key):
    # مسابقات الحظ
    if key in ["حرب العصابات", "ساعة الحظ", "القنبلة", "المزاد"]:
        win = random.random() > 0.5
        amt = random.randint(5000000, 20000000)
        return ("WIN" if win else "LOSE"), amt
    
    # مسابقات السرعة
    if key == "صيد":
        code = str(random.randint(1000, 9999))
        return f"🎯 أسرع واحد يكتب الرقم: `{code}`", code
    
    # ألعاب الأسئلة
    if key in ALL_QUESTIONS:
        if len(used_questions[key]) >= len(ALL_QUESTIONS[key]): used_questions[key] = []
        available = [q for q in ALL_QUESTIONS[key] if q not in used_questions[key]]
        q_pair = random.choice(available)
        used_questions[key].append(q_pair)
        return q_pair[0], q_pair[1]
    return None, None
