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
            'image_points': 0,    
            'msg_count': 0,       
            'roulette_wins': 0,
            'last_salary': 0,
            'last_gift': 0,
            'album': []           # حقل الألبوم الجديد لتخزين صور الموسم
        }
        db.insert(u_data)
    
    # تأكد من وجود الحقول الجديدة حتى للمستخدمين القدامى (صيانة تلقائية)
    changed = False
    fields = {
        'image_points': 0,
        'msg_count': 0,
        'album': [],             # إضافة الألبوم للمستخدمين القدامى
        'roulette_wins': 0
    }
    
    for field, default_val in fields.items():
        if field not in u_data:
            u_data[field] = default_val
            changed = True
            
    if changed:
        db.update(u_data, User.id == user_id)
        
    return u_data

# دالة لإضافة صورة للألبوم (تمنع التكرار في الألبوم نفسه)
def add_to_album(user_id, photo_id):
    u_data = db.get(User.id == user_id)
    if u_data:
        current_album = u_data.get('album', [])
        if photo_id not in current_album:
            current_album.append(photo_id)
            db.update({'album': current_album}, User.id == user_id)
            return True # تم الإضافة بنجاح
    return False # الصورة موجودة مسبقاً

def get_top_users(limit=10):
    return db.all()
