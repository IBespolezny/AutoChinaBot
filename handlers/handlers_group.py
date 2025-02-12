import asyncio
import os
import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, Message, ChatMemberAdministrator, ChatMemberOwner
import requests

import config
from database.orm_query import orm_delete_all_dialogs, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_dialog_by_client_message, orm_get_managers, orm_get_managers_group, orm_update_manager_in_dialog, orm_update_managers_group
from filters.chat_filters import ChatTypeFilter

from sqlalchemy.ext.asyncio import AsyncSession

# from keybords.inline_kbds import get_callback_btns
from functions.functions import get_admins_and_managers
from handlers.handlers_user import Statess
import handlers.handlers_user as HU
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row
from keybords.return_kbds import main_menu, hot_menu, question_menu


#######################################  Фильтр групп   #########################################

managers_group_router = Router()
managers_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))
bot = Bot(token=os.getenv("API_TOKEN"))

class MainManagerFilter(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        return message.chat.id == await orm_get_managers_group(session)

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

    # Получаем информацию о боте в чате
    chat_member = await bot.get_chat_member(message.chat.id, bot.id)
    # Проверяем, является ли бот администратором или владельцем чата
    if isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner)):
        if chat_member.can_delete_messages:
            try:
                await message.delete()
            except Exception as e:
                await message.answer("⚠️ Не удалось удалить сообщение. Возможно, оно слишком старое.")

            admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
            if message.from_user.id in admins_ids:
                await orm_delete_all_dialogs(session)
                await message.answer("Данные удалены!\n\n Клиенты больше не побеспокоят😉\n\nНужно чистить данные через некоторый промежуток времени...")
            else:
                await message.answer("У вас недостаточно прав, команда доступна только Администраторам!")
        else:
            await message.answer("⚠️ Бот не имеет прав на удаление сообщений. Проверьте права администратора.")
    else:
        await message.answer("⚠️ Бот не является администратором в этом чате. Добавьте права администратора.")



@managers_group_router.message(Command("set_group"))
async def inline_button_handler_exchange(message: types.Message, state: FSMContext, session: AsyncSession):
    # Получаем информацию о боте в чате
    chat_member = await bot.get_chat_member(message.chat.id, bot.id)
    
    # Проверяем, является ли бот администратором или владельцем чата
    if isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner)):
        if chat_member.can_delete_messages and chat_member.can_pin_messages:
            try:
                await message.delete()
            except Exception:
                await message.answer("⚠️ Не удалось удалить сообщение. Возможно, оно слишком старое.")
            
            # Обновляем ID группы в базе данных
            await orm_update_managers_group(session, message.chat.id)
            
            # Отправляем инструкцию и закрепляем сообщение
            sent_message = await message.answer(config.INSTRUCTION, parse_mode='HTML')
            try:
                await bot.pin_chat_message(message.chat.id, sent_message.message_id)
            except Exception:
                await message.answer("⚠️ Не удалось закрепить сообщение. Проверьте права бота.")
            
            await message.answer("✅ Группа установлена и инструкция закреплена!")
        else:
            await message.answer("⚠️ Бот не имеет прав на удаление или закрепление сообщений. Проверьте права администратора.")
    else:
        await message.answer("⚠️ Бот не является администратором в этом чате. Добавьте права администратора.")




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

        
