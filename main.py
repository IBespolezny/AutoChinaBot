import os
from aiogram import Bot, Dispatcher, types, F
import asyncio

from dotenv import find_dotenv, load_dotenv

from database.engine import create_db, drop_db, session_maker, engine
from database.models import Admin, Cars, DefQuestion, Dialog, Manager, ManagersGroup
from functions.functions import create_calculate_table_with_defaults, create_specific_table
from handlers.handlers_user import user_router_manager
from handlers.handlers_admin import admin_router
from handlers.handlers_group import managers_group_router

from handlers.handlers_admin_calculate import admin_calculate_router
from handlers.handlers_admin_auto_base import admin_auto_base_router
from handlers.handlers_admin_faq import admin_faq_router
from handlers.handlers_admin_edit_cars import admin_edit_cars

from handlers.handlers_user_select_auto import user_select_car
from handlers.handlers_user_calculate_auto import user_calculate_router
from handlers.handlers_user_find_auto import user_find_auto

import logging

from middlewares.db import DataBaseSession

load_dotenv(find_dotenv())
# Настройка логирования для отслеживания работы бота
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOW_UPDATES = ['message', 'edited_message', 'callback_query']     # Какие обновления обрабатываются при пулинге

bot = Bot(token=os.getenv("API_TOKEN"))
# bot.my_admins_list = []                 # Список админов бота
dp = Dispatcher()
dp.include_routers(managers_group_router)       # Подключение диспетчера для групп
dp.include_routers(admin_router)                # Подключение диспетчера для добавления ролей
dp.include_routers(admin_auto_base_router)      # Подключение диспетчера для управления базой автомобилей
dp.include_routers(admin_faq_router)            # Подключение диспетчера для управления частыми вопросами
dp.include_routers(admin_calculate_router)      # Подключение диспетчера для расчёта стоимости автомобилей
dp.include_routers(admin_edit_cars)             # Подключение диспетчера для расчёта стоимости автомобилей
dp.include_routers(user_select_car)             # Подключение диспетчера для приватного чата
dp.include_routers(user_calculate_router)       # Подключение диспетчера для приватного чата
dp.include_routers(user_find_auto)              # Подключение диспетчера для приватного чата
dp.include_routers(user_router_manager)         # Подключение диспетчера для приватного чата

# Команды для приватных чатов
commands = [
    types.BotCommand(command="start", description="Начать диалог"),
]

# Команды для групповых чатов
commands_group = [
    # types.BotCommand(command="get_id", description="Получить id пользователя"),
    # types.BotCommand(command="get_group_id", description="Получить id группы"),
    # types.BotCommand(command="cash", description="Удаляет данные сообщений клиентов"),
]

async def on_startup(bot):

    await create_specific_table(engine, Cars)
    await create_specific_table(engine, Dialog)
    await create_specific_table(engine, DefQuestion)
    await create_specific_table(engine, Manager)
    await create_specific_table(engine, Admin)
    await create_specific_table(engine, ManagersGroup)
    await create_calculate_table_with_defaults(engine)

async def on_shutdown(bot):
    print("бот закончил работу")


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands, scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands_group, scope=types.BotCommandScopeAllGroupChats())
    await dp.start_polling(bot, allowed_updates=ALLOW_UPDATES, )
    

if __name__ == '__main__':
    
    asyncio.run(main())
