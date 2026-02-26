from config import ALLOWED_GROUPS

def check_allowed_group(chat_id):
    return chat_id in ALLOWED_GROUPS
