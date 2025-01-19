import asyncio
import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, Message, InlineKeyboardMarkup, InlineKeyboardButton
import requests

import config
from database.orm_query import orm_add_dialog, orm_end_dialog, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_dialog_by_client_message, orm_get_managers, orm_save_client_message, orm_update_manager_in_dialog
from database.models import Dialog
from filters.chat_filters import ChatTypeFilter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# from keybords.inline_kbds import get_callback_btns
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row
from keybords.return_kbds import main_menu, hot_menu, question_menu

#######################################  Класс состояний  ###################################################

messages = {}

class Statess(StatesGroup):
    Order = State()                         # Состояние Любое сообщение от клиента


#######################################  Фильтр групп   #########################################

user_router_manager = Router()
user_router_manager.message.filter(ChatTypeFilter(['private']))
bot = Bot(token=config.API_TOKEN)


#######################################     Статичные Команды    ###########################################

@user_router_manager.message(StateFilter('*'), Command("start"))            # Очищает Машину состояний
async def start_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(config.START_MESSAGE, reply_markup=main_menu.as_markup(
                            resize_keyboard=True), parse_mode='HTML')

