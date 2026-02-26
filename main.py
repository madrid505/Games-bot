import asyncio
from telegram.ext import Application
from core.security import check_allowed_group
from core.permissions import is_owner_or_admin
from games.quiz import QuizGame
from roulette.roulette import RouletteGame
from bank.bank import BankSystem
from config import BOT_TOKEN

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة Handlers
    QuizGame.register_handlers(app)
    RouletteGame.register_handlers(app)
    BankSystem.register_handlers(app)

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
