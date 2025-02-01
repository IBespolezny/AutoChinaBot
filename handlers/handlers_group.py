import asyncio
import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, Message
import requests

import config
from database.orm_query import orm_delete_all_dialogs, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_dialog_by_client_message, orm_get_managers, orm_update_manager_in_dialog
from filters.chat_filters import ChatTypeFilter

from sqlalchemy.ext.asyncio import AsyncSession

# from keybords.inline_kbds import get_callback_btns
from handlers.handlers_user import Statess
import handlers.handlers_user as HU
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row
from keybords.return_kbds import main_menu, hot_menu, question_menu


#######################################  Фильтр групп   #########################################

managers_group_router = Router()
managers_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))
bot = Bot(token=config.API_TOKEN)

class MainManagerFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == config.MANAGERS_GROUP_ID

#######################################     Статичные Команды    ###########################################

@managers_group_router.message(StateFilter('*'), Command("get_group_id"))            # Очищает Машину состояний
async def start_handler(message: types.Message, state: FSMContext) -> None:
    group_id = message.chat.id
    await message.answer(f"<b>ID группы:</b> <code>{group_id}</code>", parse_mode='HTML')


@managers_group_router.message(StateFilter('*'), Command("get_id"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"<b>Ваш ID:</b> <code>{user_id}</code>", parse_mode='HTML')


@managers_group_router.message(StateFilter('*'), Command("cash"))
async def send_welcome(message: types.Message, session: AsyncSession):
    # await message.delete()
    await orm_delete_all_dialogs(session)
    await message.answer("Данные удалены!\n\n Клиенты больше не побеспокоят😉\n\nНужно чистить данные через некоторый промежуток времени...")


@managers_group_router.message(StateFilter('*'), Command("set_group"))
async def send_welcome(message: types.Message, session: AsyncSession):
    await message.delete()
    config.MANAGERS_GROUP_ID = message.chat.id
    await message.answer("✅ Группа установлена!")

@managers_group_router.message(StateFilter('*'), MainManagerFilter(), F.reply_to_message)  # Обработчик ответов менеджера
async def caught_query(message: types.Message, state: FSMContext, session: AsyncSession):
    # Получаем ID сообщения, на которое отвечает менеджер
    replied_message_id = message.reply_to_message.message_id
    # Получаем диалог из базы данных по ID сообщения клиента
    dialog = await orm_get_dialog_by_client_message(session, client_message_id=replied_message_id)

    if dialog:
        # Отправляем текст ответа клиенту
        sent_message = await bot.send_message(chat_id=dialog.client_id, text=f"<b>{message.from_user.first_name}</b>:\n{message.text}", parse_mode='HTML')

        # Обновляем данные о менеджере в диалоге
        await orm_update_manager_in_dialog(
            session=session,
            client_message_id=dialog.client_message_id,
            manager_id=message.from_user.id,
            manager_message_id=sent_message.message_id
        )
    else:
        await message.answer("Диалог не найден. Убедитесь, что сообщение связано с клиентским запросом.")

        
