import os
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

# 📂 إعداد المسار لضمان حفظ البيانات عند إعادة التشغيل مع دعم الـ Volume
db_dir = '/app/data'
db_path = os.path.join(db_dir, 'bank_data.json')

# تأكد من وجود المجلد، وإذا فشل (بسبب الصلاحيات)، انتقل للمسار المحلي
if not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir)
    except:
        db_path = 'bank_data.json'

# استخدام CachingMiddleware لزيادة سرعة الكتابة وتقليل مشاكل الـ I/O مع الـ Volumes
db = TinyDB(db_path, storage=CachingMiddleware(JSONStorage), ensure_ascii=False)
User = Query()

async def get_user_data(update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    
    # 🛑 حالة مستخدم جديد
    if not u_data:  
        # رصيد المطور (تم تحديثه)
        balance = 999999999999999999 if user_id == 5010882230 else 1000000000000
        
        u_data = {
            'id': user_id,
            'name': update.effective_user.first_name,
            'balance': balance,
            'points': 0,
            'image_points': 0,
            'weekly_pts': 0,
            'msg_count': 0,
            'roulette_wins': 0,
            'last_salary': 0,
            'last_gift': 0,
            'album': [],
            'card_counter': 0
        }
        db.insert(u_data)
    else:
        # تحديث رصيد المالك يدوياً
        if user_id == 5010882230:
            db.update({'balance': 999999999999999999}, User.id == user_id)
            u_data['balance'] = 999999999999999999
            
        # 🆕 التحديث التلقائي للبيانات (Migration)
        updates = {}
        if 'image_points' not in u_data: updates['image_points'] = 0
        if 'weekly_pts' not in u_data: updates['weekly_pts'] = 0
        if 'album' not in u_data: updates['album'] = []
        if 'card_counter' not in u_data: updates['card_counter'] = 0
        if 'last_salary' not in u_data: updates['last_salary'] = 0
        
        if updates:
            db.update(updates, User.id == user_id)
            u_data = db.get(User.id == user_id)
            
    return u_data

# --- وظائف التحكم في البيانات ---

def add_to_album(user_id, card_id):
    u_data = db.get(User.id == user_id)
    if u_data:
        current_album = u_data.get('album', [])
        current_album.append(card_id)
        db.update({'album': current_album}, User.id == user_id)
        return True
    return False

def update_card_counter(user_id, count):
    db.update({'card_counter': count}, User.id == user_id)

def reset_weekly_points():
    # تصفير النقاط لكل المستخدمين
    db.update({'weekly_pts': 0}, User.id.exists())

def get_top_users(limit=10):
    return sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:limit]
