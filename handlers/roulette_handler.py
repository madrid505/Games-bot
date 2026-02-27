import random
from strings import ROULETTE_MESSAGES
from config import OWNER_ID

async def handle_roulette(update, context, text, u_id, u_name):
    if text == "انا" and context.chat_data.get('r_on'):
        if 'r_players' not in context.chat_data: context.chat_data['r_players'] = []
        context.chat_data['r_players'].append({'id': u_id, 'name': u_name})
        await update.message.reply_text(ROULETTE_MESSAGES["register"].format(u_name=u_name))
        return True
    
    if text == "روليت":
        admins = [a.user.id for a in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if u_id == OWNER_ID or u_id in admins:
            context.chat_data['r_on'], context.chat_data['r_players'], context.chat_data['r_starter'] = True, [], u_id
            await update.message.reply_text(ROULETTE_MESSAGES["start"])
        return True
    return False
