import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand  # Добавьте этот импорт

from dotenv import load_dotenv
import os

from app.user import user
from app.admin import admin


from app.database.models import async_main


async def main():
    load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'))
    
    await set_commands(bot)
    dp = Dispatcher()
    dp.include_routers(user, admin)
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    
    await dp.start_polling(bot)



async def set_commands(bot: Bot):
    commands = [

        BotCommand(command="menu", description="Показать меню пользователя"),
        # Другие команды...
    ]
    await bot.set_my_commands(commands)

async def startup(dispatcher: Dispatcher):
    await async_main()
    print('Starting up...')


async def shutdown(dispatcher: Dispatcher):
    print('Shutting down...')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass