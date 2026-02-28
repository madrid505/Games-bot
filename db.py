import os
from tinydb import TinyDB, Query

# 📂 الربط مع المجلد الدائم الذي أنشأته في Northflank
# Container mount path: /app/data
db_dir = '/app/data'
db_path = os.path.join(db_dir, 'bank_data.json')

# التأكد من وجود المجلد (للحماية البرمجية)
if not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir)
    except:
        # إذا كنت تجرب الكود محلياً على جهازك الشخصي
        db_path = 'bank_data.json'

# استخدام TinyDB للحفظ التلقائي الفوري
db = TinyDB(db_path)
User = Query()

async def get_user_data(update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    
    if not u_data:
        # إعدادات المستخدم الجديد (المالك 1 ترليون، اللاعبين 10 مليار)
        balance = 1000000000000 if user_id == 5010882230 else 10000000000
        u_data = {
            'id': user_id,
            'name': update.effective_user.first_name,
            'balance': balance,
            'points': 0,
            'image_points': 0,    # نقاط ألعاب الصور
            'msg_count': 0,       # عداد ملك التفاعل
            'roulette_wins': 0,   # انتصارات الروليت
            'last_salary': 0,     # وقت آخر راتب
            'last_gift': 0,       # وقت آخر هدية
            'album': []           # ألبوم الصور المكتسبة
        }
        db.insert(u_data)
    else:
        # 🛠️ صيانة تلقائية: إضافة الحقول الجديدة للمستخدمين القدامى دون مس رصيدهم
        updates = {}
        if 'image_points' not in u_data: updates['image_points'] = 0
        if 'msg_count' not in u_data: updates['msg_count'] = 0
        if 'album' not in u_data: updates['album'] = []
        if 'roulette_wins' not in u_data: updates['roulette_wins'] = 0
        
        if updates:
            db.update(updates, User.id == user_id)
            u_data = db.get(User.id == user_id) # إعادة القراءة للتأكد من التحديث
            
    return u_data

# دالة إضافة صورة للألبوم (تمنع التكرار لضمان صعوبة التجميع)
def add_to_album(user_id, photo_id):
    u_data = db.get(User.id == user_id)
    if u_data:
        current_album = u_data.get('album', [])
        if photo_id not in current_album:
            current_album.append(photo_id)
            db.update({'album': current_album}, User.id == user_id)
            return True # تم إضافة بطاقة جديدة بنجاح
    return False # البطاقة موجودة مسبقاً

# دالة جلب المتصدرين
def get_top_users(limit=10):
    return db.all()
