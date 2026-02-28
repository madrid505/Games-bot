# db.py
from tinydb import TinyDB, Query
import time

db = TinyDB('bank_data.json')
User = Query()

async def get_user_data(update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    if not u_data:
        # المالك رصيد ضخم، واللاعبين 10 مليار كبداية
        balance = 1000000000000 if user_id == 5010882230 else 10000000000
        u_data = {
            'id': user_id,
            'name': update.effective_user.first_name,
            'balance': balance,
            'points': 0,
            'image_points': 0,    # أضفنا حقل نقاط الصور
            'msg_count': 0,       # أضفنا حقل ملك التفاعل
            'roulette_wins': 0,
            'last_salary': 0,
            'last_gift': 0
        }
        db.insert(u_data)
    
    # تأكد من وجود الحقول الجديدة حتى للمستخدمين القدامى
    changed = False
    if 'image_points' not in u_data:
        u_data['image_points'] = 0
        changed = True
    if 'msg_count' not in u_data:
        u_data['msg_count'] = 0
        changed = True
    if changed:
        db.update(u_data, User.id == user_id)
        
    return u_data

# دالة جلب الترتيب (ضرورية لدفتر النتائج)
def get_top_users(limit=10):
    all_users = db.all()
    # نرجع كل المستخدمين ليتم ترتيبهم داخل الـ handler حسب نوع اللعبة
    return all_users
