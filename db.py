import os
from tinydb import TinyDB, Query

# 📂 إعداد المسار لضمان حفظ البيانات عند إعادة التشغيل (خاصة على Northflank)
db_dir = '/app/data'
if not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir)
        db_path = os.path.join(db_dir, 'bank_data.json')
    except:
        db_path = 'bank_data.json'
else:
    db_path = os.path.join(db_dir, 'bank_data.json')

db = TinyDB(db_path)
User = Query()

async def get_user_data(update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    
    if not u_data:
        
        # 👑 رصيد المالك (كوادريليون) ورصيد الأعضاء (تريليون)
# رصيدك يبدأ بـ 999 كوادريليون، وهو رقم يصعب حتى قراءته!
balance = 999999999999999999 if user_id == 5010882230 else 1000000000000
        
        u_data = {
            'id': user_id,
            'name': update.effective_user.first_name,
            'balance': balance,
            'points': 0,          # نقاط الثقافة العامة
            'image_points': 0,    # نقاط ألعاب الصور
            'weekly_pts': 0,      # نقاط التفاعل الأسبوعية (ملوك التفاعل)
            'msg_count': 0,
            'roulette_wins': 0,
            'last_salary': 0,
            'last_gift': 0,
            'album': [],          # ألبوم البطاقات الملكية
            'card_counter': 0     # عداد الفوز للحصول على بطاقة (كل 5 فوزات)
        }
        db.insert(u_data)
    else:
        # 🆕 التحديث التلقائي للبيانات (Migration) لدعم الميزات الجديدة
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
    """إضافة بطاقة جديدة للألبوم الملكي"""
    u_data = db.get(User.id == user_id)
    if u_data:
        current_album = u_data.get('album', [])
        current_album.append(card_id)
        db.update({'album': current_album}, User.id == user_id)
        return True
    return False

def update_card_counter(user_id, count):
    """تحديث عداد البطاقات الملكية"""
    db.update({'card_counter': count}, User.id == user_id)

def reset_weekly_points():
    """تصفير نقاط التفاعل لجميع المستخدمين (تستخدم أسبوعياً)"""
    db.update({'weekly_pts': 0}, User.id.exists())

def get_top_users(limit=10):
    """جلب قائمة الأثرياء"""
    return sorted(db.all(), key=lambda x: x.get('balance', 0), reverse=True)[:limit]
