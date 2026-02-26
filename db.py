from tinydb import TinyDB, Query

db = TinyDB('bank_data.json')
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
            'roulette_wins': 0,
            'last_salary': 0
        }
        db.insert(u_data)
    return u_data
