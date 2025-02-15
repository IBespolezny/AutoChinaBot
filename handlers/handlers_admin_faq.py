import asyncio
import os
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_cars, orm_get_managers, orm_update_calculate_column
from filters.chat_filters import ChatTypeFilter
import config

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from functions.functions import get_admins_and_managers
from handlers.handlers_user import Statess
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row, get_custom_callback_btns, orm_delete_car_buttons
from keybords.return_kbds import admin_menu, access_settings, admin_settings, manager_settings, auto_settings, add_del_back_menu
# from keybords.inline_kbds import get_callback_btns

bot = Bot(token=os.getenv("API_TOKEN"))


#################################   Фильтр групп   #################################

admin_faq_router = Router()
admin_faq_router.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())


############################################ кнопка "Частые вопросы" ############################################

@admin_faq_router.message(Statess.Admin_kbd, F.text.casefold().contains("частые вопросы"))  # Обработка кнопки "частые вопросы"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.answer("Выберите действие:", reply_markup=add_del_back_menu.as_markup(
                            resize_keyboard=True))
    await state.set_state(Statess.DefQuestion_set)


@admin_faq_router.message(Statess.DefQuestion_set, F.text.casefold().contains("добавить"))  # Добавление вопроса
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.answer("Введите новый вопрос:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.DefQuestion_add)


@admin_faq_router.message(Statess.DefQuestion_add, F.text)  # Добавление вопроса
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    question = message.text
    await message.delete()

    await state.update_data(question = question)
    await message.answer("Введите ответ на вопрос:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.add_DefAnswer)


@admin_faq_router.message(Statess.add_DefAnswer, F.text)  # Добавление ответа
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await state.update_data(answer = message.text)
    await message.delete()

    vokeb = await state.get_data()

    await orm_add_DefQuestion(session, vokeb)
    await state.set_state(Statess.DefQuestion_set)
    await message.answer("Добавлен новый вопрос!", reply_markup=add_del_back_menu.as_markup(
                            resize_keyboard=True))


@admin_faq_router.message(Statess.DefQuestion_set, F.text.casefold().contains("удалить"))  # Удаление вопроса
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    questions = await orm_get_DefQuestions(session) # Получение админов из БД

    questionss = {question.question: f"delQuestion_{question.id}" for question in questions}
    questionss["Назад"] = "questions_"

    await message.answer("Выберите вопрос для удаления:", reply_markup=get_callback_btns_single_row(btns=questionss, sizes=(1,)))


@admin_faq_router.callback_query(F.data.startswith("delQuestion_")) # Обаботчик для удаления Вопроса по id
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession):
    # Удаляем сообщение с клавиатурой
    await callback.message.delete()
    question = callback.data.replace("delQuestion_", "")

    await orm_delete_DefQuestion(session, int(question))
    await callback.message.answer("Вопрос удалён!")


@admin_faq_router.message(Statess.DefQuestion_set, F.text.casefold().contains("назад"))  # Обработка кнопки "Назад"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Statess.Admin_kbd)
    await message.answer("Выберите вариант", reply_markup=admin_menu.as_markup(
                            resize_keyboard=True))
    
@admin_faq_router.callback_query(F.data.startswith("questions_")) # Обаботчик для удаления Вопроса по id
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Statess.DefQuestion_set)