import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, Message, InlineKeyboardMarkup, InlineKeyboardButton
import requests

import config
from database.orm_query import orm_add_dialog, orm_end_dialog, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_calculate_column_value, orm_get_car, orm_get_car_by_flag, orm_get_cars_by_cost, orm_get_dialog_by_client_id, orm_get_dialog_by_client_message, orm_get_electrocars, orm_get_managers, orm_get_managers_group, orm_save_client_message, orm_update_manager_in_dialog
from database.models import Dialog
from filters.chat_filters import ChatTypeFilter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# from keybords.inline_kbds import get_callback_btns
from functions.functions import format_number, get_admins_and_managers, int_format, is_valid_phone_number
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row, get_custom_callback_btns
from keybords.return_kbds import main_menu, hot_menu, question_menu, region_menu, engine_menu, old_or_new_menu

#######################################  Класс состояний  ###################################################

messages = {}

class Statess(StatesGroup):
    Order = State()                         # Состояние Любое сообщение от клиента
    add_admin_name = State()                # Состояние Добавление имени админа
    add_admin_id = State()                  # Состояние Добавление ID админа
    help_buy_auto = State()                  # Состояние Добавление ID админа
    Admin_kbd = State()                     # Состояние клавиатуры управления доступом
    Admin_settings = State()                # Состояние управления Администраторами
    enter_cost = State()                # Состояние управления Администраторами
    Manager_settings = State()              # Состояние управления Менеджерами
    add_manager_name = State()              # Состояние добавления Имени менеджера
    add_manager_id = State()                # Состояние добавления ID менеджера
    Cars_by_cost_set = State()                  # Состояние клавиатуры машин по стоимости
    Popular_cars_set = State()                  # Состояние клавиатуры машин по популярности
    Electrocars_set = State()                   # Состояние клавиатуры электрокаров
    Cars_quee_set = State()                     # Состояние клавиатуры автомобилей в пути
    Сars_in_set = State()                       # Состояние клавиатуры автомобилей в наличии
    DefQuestion_set = State()                   # Состояние клавиатуры частого вопроса
    add_DefAnswer = State()                     # Состояние добавления частого ответа
    DefQuestion_add = State()                   # Состояние добавления частого вопроса
    delete_auto = State()                   # Состояние добавления частого вопроса
    ask_question = State()                      # Состояние записи вопроса для менеджера
    consultation = State()                      # Состояние формирования заказа

    choos_region = State()                      # Состояние формирования заказа
    enter_engine_type = State()                      # Состояние формирования заказа
    enter_phone_number = State()                      # Состояние формирования заказа
    Write_sum = State()                      # Состояние формирования заказа

    Mark = State()                              # Добавление марки авто
    Model = State()                              # Добавление модели авто
    Year = State()                              # Добавление года авто
    engine = State()                              # Добавление года авто
    engine_volume = State()                              # Добавление года авто
    route = State()                              # Добавление года авто
    rools = State()                              # Добавление года авто
    power = State()                              # Добавление года авто
    power_engin = State()                              # Добавление года авто
    photo = State()                              # Добавление года авто
    flag = State()                              # Добавление года авто
    electrocar = State()                              # Добавление года авто
    cost = State()                              # Добавление года авто
    power_bank = State()                              # Добавление года авто
    package = State()                              # Добавление года авто
    body = State()                              # Добавление года авто
    power_reserve = State()                              # Добавление года авто


#######################################  Фильтр групп   #########################################

user_router_manager = Router()
user_router_manager.message.filter(ChatTypeFilter(['private']))
bot = Bot(token=os.getenv("API_TOKEN"))



#######################################     Статичные Команды    ###########################################

@user_router_manager.message(StateFilter('*'), Command("start"))            # Очищает Машину состояний
async def start_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(config.START_MESSAGE, reply_markup=main_menu.as_markup(
                            resize_keyboard=True), parse_mode='HTML')


@user_router_manager.message(F.text.casefold().contains("назад"))  # Обработка кнопки "назад"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    await message.answer("Главное меню🔙", reply_markup=main_menu.as_markup(
                            resize_keyboard=True))









#######################################     Вопросы и ответы    ###########################################

@user_router_manager.message(F.text.casefold().contains("вопросы и ответы"))   # Логика Вопросы и ответы
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите тип вопроса❔", reply_markup=question_menu.as_markup(
                            resize_keyboard=True))
    






#######################################     Частые вопросы    ###########################################


@user_router_manager.message(F.text.casefold().contains("частые вопросы"))  # Логика Частые вопросы
async def hot_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    # Получение списка частых вопросов
    def_questions = await orm_get_DefQuestions(session)
    
    # Формирование словаря для клавиатуры
    question_btns = {question.question: f"question_{question.id}" for question in def_questions}
    
    # Отправка сообщения с кнопками
    questionMessage = await message.answer(
        "Список Частых Вопросов:",
        reply_markup=get_callback_btns_single_row(btns=question_btns, sizes=(1,))
    )
    await state.update_data(questionMessage = questionMessage.message_id)



@user_router_manager.callback_query(F.data.startswith("question_")) # Обаботчик для удаления списка Менеджеров
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    answerID = callback.data.removeprefix("question_")
    answer = await orm_get_DefQuestion(session, int(answerID))
    
    def_questions = await orm_get_DefQuestions(session)                                             # Получение списка частых вопросов
    
    question_btns = {question.question: f"question_{question.id}" for question in def_questions}    # Формирование словаря для клавиатуры

    vokeb = await state.get_data()
    questionMessage = int(vokeb.get("questionMessage"))
    await bot.edit_message_text(answer.answer, callback.message.chat.id, questionMessage,           # Редактирование сообщения с вопросами
                                reply_markup=get_callback_btns_single_row(btns=question_btns, sizes=(1,))) 






#######################################     Задать вопрос    ###########################################

@user_router_manager.message(F.text.casefold().contains("задать вопрос"))   # Логика Задать вопрос
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Введите свой вопрос:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.ask_question)



@user_router_manager.message(Statess.ask_question, F.text)   # Логика Задать вопрос
async def hot_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    mesID = message.message_id  # ID исходного сообщения клиента
    delmes = await message.answer("Поиск свободного менеджера...")
    await bot.send_message(chat_id=await orm_get_managers_group(session), text = "❓Вопрос от клиента\n\n⬇️Ссылка на клиента⬇️")
    # Пересылаем сообщение клиента в группу менеджеров
    forwarded_message = await bot.forward_message(
        chat_id=await orm_get_managers_group(session), 
        from_chat_id=message.chat.id, 
        message_id=mesID
    )
    
    # Добавляем диалог в базу данных, используя ID пересланного сообщения
    await orm_add_dialog(
        session, 
        client_id=message.from_user.id, 
        client_message_id=forwarded_message.message_id  # ID пересланного сообщения
    )
    await bot.delete_message(message.chat.id, delmes.message_id)
    await message.answer(
        f"Ваш вопрос:\n<b>{message.text}</b>\nотправлен менеджерам✅\nОжидайте ответ🕜\nЕсли вам нужно продолжить искать автомобиль, пока ожидаете ответ, используйте команду /start", 
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Закончить диалог", callback_data=f"end_{mesID}")]
            ]
        ),
        parse_mode='HTML'
    )
    await state.clear()



@user_router_manager.callback_query(StateFilter('*'), F.data.startswith("end_"))  # Обработка inline-кнопки "Завершить диалог"
async def start_handler(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()
    user_id = callback.message.chat.id
    user_name = callback.from_user.full_name

    # Получаем диалог по client_message_id
    dialog = await orm_get_dialog_by_client_id(session, user_id)

    if dialog and dialog.manager_id:
        await bot.send_message(int(dialog.manager_id), f"Пользователь {user_name} завершил диалог.")


    # Завершаем диалог
    await orm_end_dialog(session, client_id=user_id)

    # Сообщаем пользователю
    await callback.message.answer(
        "Диалог завершён!",
        reply_markup=main_menu.as_markup(resize_keyboard=True)
    )



@user_router_manager.message(F.text == "/end", F.reply_to_message)  # Команда /end при ответе на сообщение
async def end_dialog_with_reply(message: types.Message, session: AsyncSession, bot: Bot) -> None:
    # Проверяем, есть ли ответное сообщение
    replied_message = message.reply_to_message

    if not replied_message:
        await message.reply("❌ Эта команда должна быть ответом на сообщение клиента.")
        return

    # Получаем информацию о диалоге из базы данных по ID пересланного сообщения
    dialog = await orm_get_dialog_by_client_message(session, client_message_id=replied_message.message_id)

    if not dialog:
        await message.reply("❌ Диалог не найден в базе данных.")
        return

    # Извлекаем ID клиента из найденного диалога
    client_id = dialog.client_id

    if not client_id:
        await message.reply("❌ Не удалось определить ID клиента.")
        return

    # Уведомляем клиента о завершении диалога
    try:
        await bot.send_message(
            chat_id=client_id,
            text="Диалог завершён менеджером. Спасибо за обращение!",
            reply_markup=main_menu.as_markup(resize_keyboard=True)
        )
    except Exception:
        await message.reply("⚠️ Не удалось отправить уведомление клиенту, возможно, он ограничил сообщения от ботов.")

    # Завершаем диалог в базе данных
    await orm_end_dialog(session, client_id=client_id)

    # Уведомляем менеджера о завершении
    await message.reply("✅ Диалог завершён.")



@user_router_manager.message(StateFilter('*'),  F.reply_to_message)  # Обработчик ответов менеджера в чате с ботом
async def caught_query(message: types.Message, state: FSMContext, session: AsyncSession):
    managers = await orm_get_managers(session) # Получение менеджеров из БД
    managerss = {manager.name : f"{manager.id}" for manager in managers}
    managers = [int(manager) for manager in managerss.values()]

    if message.from_user.id not in managers:
        await message.delete()
        await message.answer("❌Не нужно отвечать на сообщения, пишите в чат", reply_markup=main_menu.as_markup(
                            resize_keyboard=True))
        return

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
        await message.answer("Диалог не найден. Убедитесь, что вы отвечаете на нужное сообщение", reply_markup=main_menu.as_markup(
                            resize_keyboard=True))


@user_router_manager.message()  # Логика ответа на вопрос клиента
async def hot_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    # Проверяем, есть ли активный диалог
    query = (
        select(Dialog)
        .where(Dialog.client_id == message.chat.id, Dialog.is_active == True)
    )
    result = await session.execute(query)
    dialog = result.scalar()

    if dialog and dialog.manager_id:
        # Пересылаем сообщение менеджеру
        forwarded_message = await bot.forward_message(
            chat_id=dialog.manager_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Сохраняем пересланное сообщение в таблицу
        await orm_save_client_message(
            session=session,
            client_id=message.chat.id,
            manager_id=dialog.manager_id,
            client_message_id=forwarded_message.message_id,
            manager_message_id=message.message_id
        )

    else:
        await message.reply("Диалог с менеджером не найден. Желаете задать вопрос?", reply_markup=question_menu.as_markup(
                            resize_keyboard=True))
