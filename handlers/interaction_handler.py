from db import get_user_data, db, User

async def update_interaction(update, u_id):
    try:
        u_data = await get_user_data(update)
        current_count = u_data.get('msg_count', 0) + 1
        db.update({'msg_count': current_count}, User.id == u_id)
        return True
    except Exception as e:
        print(f"❌ خطأ في ملك التفاعل: {e}")
        return False
