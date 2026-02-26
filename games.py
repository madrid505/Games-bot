# games.py
import random

# هيكل الـ 100 سؤال (مكررة برمجياً للتجربة، استبدلها بأسئلتك الفريدة)
ALL_QUESTIONS = {
    "دين": [("من هو أول المؤذنين؟", "بلال بن رباح"), ("أطول سورة؟", "البقرة")] * 50,
    "عواصم": [("عاصمة الأردن؟", "عمان"), ("عاصمة فلسطين؟", "القدس")] * 50,
    "اندية": [("النادي الملكي؟", "ريال مدريد"), ("نادي القرن؟", "الاهلي")] * 50
}

used_questions = {k: [] for k in ALL_QUESTIONS.keys()}

async def get_game_data(game_key):
    # مسابقات الحظ والسرعة
    if game_key == "تخمين":
        num = str(random.randint(1, 10))
        return "🎲 خمن رقم من 1 إلى 10:", num
    if game_key == "صيد":
        code = str(random.randint(1000, 9999))
        return f"🎯 أسرع واحد يكتب الرقم: `{code}`", code
    
    # مسابقات الربح والخسارة الفورية
    if game_key in ["حرب العصابات", "السلم والحية", "المزاد"]:
        win = random.choice([True, False])
        amt = random.randint(5000000, 15000000)
        return ("WIN" if win else "LOSE"), amt

    # ألعاب الأسئلة (نظام الـ 100)
    if game_key in ALL_QUESTIONS:
        if len(used_questions[game_key]) >= len(ALL_QUESTIONS[game_key]):
            used_questions[game_key] = []
        available = [q for q in ALL_QUESTIONS[game_key] if q not in used_questions[game_key]]
        q_pair = random.choice(available)
        used_questions[game_key].append(q_pair)
        return q_pair[0], q_pair[1]
    
    return None, None
