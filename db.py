import os
from tinydb import TinyDB, Query

# 📂 الربط مع المجلد الدائم في Northflank
db_dir = '/app/data'
db_path = os.path.join(db_dir, 'bank_data.json')

if not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir)
    except:
        db_path = 'bank_data.json'

db = TinyDB(db_path)
User = Query()

async def get_user_data(update):
    user_id = update.effective_user.id
    u_data = db.get(User.id == user_id)
    
    if not u_data:
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
            'album': [],
            'card_counter': 0    # 🆕 الحقل الجديد لتجميع نقاط البطاقة
        }
        db.insert(u_data)
    else:
        updates = {}
        if 'image_points' not in u_data: updates['image_points'] = 0
        if 'msg_count' not in u_data: updates['msg_count'] = 0
        if 'album' not in u_data: updates['album'] = []
        if 'roulette_wins' not in u_data: updates['roulette_wins'] = 0
        if 'card_counter' not in u_data: updates['card_counter'] = 0 # 🆕 صيانة للقدامى
        
        if updates:
            db.update(updates, User.id == user_id)
            u_data = db.get(User.id == user_id)
            
    return u_data

def add_to_album(user_id, photo_id):
    u_data = db.get(User.id == user_id)
    if u_data:
        current_album = u_data.get('album', [])
        if photo_id not in current_album:
            current_album.append(photo_id)
            db.update({'album': current_album}, User.id == user_id)
            return True 
    return False 

# دالة لتحديث عداد نقاط البطاقات
def update_card_counter(user_id, count):
    db.update({'card_counter': count}, User.id == user_id)

def get_top_users(limit=10):
    return db.all()
