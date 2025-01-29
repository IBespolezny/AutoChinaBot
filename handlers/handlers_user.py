import asyncio
import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, Message, InlineKeyboardMarkup, InlineKeyboardButton
import requests

import config
from database.orm_query import orm_add_dialog, orm_end_dialog, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_car, orm_get_car_by_flag, orm_get_dialog_by_client_message, orm_get_electrocars, orm_get_managers, orm_save_client_message, orm_update_manager_in_dialog
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
    add_admin_name = State()                # Состояние Добавление имени админа
    add_admin_id = State()                  # Состояние Добавление ID админа
    Admin_kbd = State()                     # Состояние клавиатуры управления доступом
    Admin_settings = State()                # Состояние управления Администраторами
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
    ask_question = State()                      # Состояние записи вопроса для менеджера
    consultation = State()                      # Состояние формирования заказа

    Mark = State()                              # Добавление марки авто
    Model = State()                              # Добавление модели авто
    Year = State()                              # Добавление года авто
    engine = State()                              # Добавление года авто
    engine_volume = State()                              # Добавление года авто
    route = State()                              # Добавление года авто
    engine_type = State()                              # Добавление года авто
    power = State()                              # Добавление года авто
    photo = State()                              # Добавление года авто
    flag = State()                              # Добавление года авто
    electrocar = State()                              # Добавление года авто
    cost = State()                              # Добавление года авто
    power_bank = State()                              # Добавление года авто
    package = State()                              # Добавление года авто
    body = State()                              # Добавление года авто


#######################################  Фильтр групп   #########################################

user_router_manager = Router()
user_router_manager.message.filter(ChatTypeFilter(['private']))
bot = Bot(token=config.API_TOKEN)

# class MainManagerFilter(BaseFilter):
#     async def __call__(self, message: Message) -> bool:
#         return message.chat.id == config.MANAGERS_GROUP_ID

#######################################     Статичные Команды    ###########################################

@user_router_manager.message(StateFilter('*'), Command("start"))            # Очищает Машину состояний
async def start_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(config.START_MESSAGE, reply_markup=main_menu.as_markup(
                            resize_keyboard=True), parse_mode='HTML')




#######################################     Подобрать автомобиль    ###########################################

@user_router_manager.message(F.text.casefold().contains("подобрать автомобиль"))   # Логика Подобрать автомобиль
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Напишите ваши пожелания по автомобилю🚗\nЧтобы наши менеджеры могли правильно подобрать вам авто", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.consultation)


@user_router_manager.message(Statess.consultation, F.text)   # Логика Задать вопрос
async def hot_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    mesID = message.message_id  # ID исходного сообщения клиента
    delmes = await message.answer("Поиск свободного менеджера...")

    await bot.send_message(chat_id=config.MANAGERS_GROUP_ID, text = "❓Вопрос от клиента")
    # Пересылаем сообщение клиента в группу менеджеров
    forwarded_message = await bot.forward_message(
        chat_id=config.MANAGERS_GROUP_ID, 
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
        f"Ваш заказ:\n<b>{message.text}</b>\nотправлен менеджерам✅\nОжидайте ответ🕜\nЕсли вам нужно продолжить искать автомобиль, пока ожидаете ответ, используйте команду /start", 
        reply_markup=get_callback_btns(btns={
                'Закончить диалог': f'end_{mesID}',
            }),
        parse_mode='HTML'
    )
    await state.clear()



#######################################     Рассчитать стоимость    ###########################################

@user_router_manager.message(F.text.casefold().contains("расчитать стоимость"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("*Логика расчёта стоимости автомобиля*")







#######################################     Горячие предложения    ###########################################

@user_router_manager.message(F.text.casefold().contains("горячие предложения🔥"))   # Логика Горячие предложения
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("🚗Выберите тип автомобиля", reply_markup=hot_menu.as_markup(
                            resize_keyboard=True))
    

    
@user_router_manager.message(F.text.casefold().contains("подборка автомобилей по стоимости"))
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("*Логика подбора автомобилей*")


@user_router_manager.message(F.text.casefold().contains("популярные автомобили"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes = message.message_id)
    await state.update_data(order_chat = message.chat.id)

    cars = await orm_get_car_by_flag(session, "Популярное")  # Получаем список машин с флагом "Популярное"
    if cars:
        for car in cars:
            car_info = (
                f"🚗 **Марка:** {car.mark}\n"
                f"📍 **Модель:** {car.model}\n"
                f"📅 **Год выпуска:** {car.year}\n"
                f"⚙️ **Объём двигателя:** {car.engine_volume} л\n"
                f"👥 **Количество мест:** {car.places}\n"
                f"🏁 **Пробег:** {car.route} км\n"
                f"⛽ **Тип двигателя:** {car.engine_type}\n"
                f"🔧 **Тип коробки передач:** {car.box}\n"
                f"🔋 **Электрокар:** {'Да' if car.electrocar == 'Да' else 'Нет'}\n"
                f"💰 **Стоимость:** {car.cost:,} $.\n"
            )
            car_id = car.car_id
            # Отправляем фото с текстом
            await message.answer_photo(
                photo=car.foto, 
                caption=car_info, 
                parse_mode="Markdown", 
                reply_markup=get_callback_btns(btns={
                '⬅️': f'left_{car_id}',
                '➡️': f'right_{car_id}',
                'Заказать в один клик': f'get_{car_id}',
            }),)
    else:
        await message.answer("🚫 Популярные автомобили не найдены.")

    

@user_router_manager.message(F.text.casefold().contains("электроавтомобили"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes = message.message_id)
    await state.update_data(order_chat = message.chat.id)

    cars = await orm_get_electrocars(session)  # Получаем список машин с флагом "Популярное"
    if cars:
        for car in cars:
            car_info = (
                f"🚗 **Марка:** {car.mark}\n"
                f"📍 **Модель:** {car.model}\n"
                f"📅 **Год выпуска:** {car.year}\n"
                f"🔋 **Емкость батареи:** {car.engine_volume} л\n"
                f"👥 **Количество мест:** {car.places}\n"
                f"🏁 **Пробег:** {car.route} км\n"
                f"⛽ **Тип двигателя:** {car.engine_type}\n"
                f"🔧 **Тип коробки передач:** {car.box}\n"
                f"💰 **Стоимость:** {car.cost:,} $\n"
            )
            car_id = car.car_id
            # Отправляем фото с текстом
            await message.answer_photo(
                photo=car.foto, 
                caption=car_info, 
                parse_mode="Markdown", 
                reply_markup=get_callback_btns(btns={
                'Заказать в один клик ': f'get_{car_id}',
            }),)

    else:
        await message.answer("🚫 Электромобили не найдены автомобили не найдены.")


@user_router_manager.message(F.text.casefold().contains("автомобили в пути"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes = message.message_id)
    await state.update_data(order_chat = message.chat.id)

    cars = await orm_get_car_by_flag(session, "В пути")  # Получаем список машин с флагом "В пути"
    if cars:
        for car in cars:
            car_info = (
                f"🚗 **Марка:** {car.mark}\n"
                f"📍 **Модель:** {car.model}\n"
                f"📅 **Год выпуска:** {car.year}\n"
                f"🔋 **Объём двигателя:** {car.engine_volume} л\n"
                f"👥 **Количество мест:** {car.places}\n"
                f"🏁 **Пробег:** {car.route} км\n"
                f"⛽ **Тип двигателя:** {car.engine_type}\n"
                f"🔧 **Тип коробки передач:** {car.box}\n"
                f"💰 **Стоимость:** {car.cost:,} $\n"
            )
            car_id = car.car_id
            # Отправляем фото с текстом
            await message.answer_photo(
                photo=car.foto, 
                caption=car_info, 
                parse_mode="Markdown", 
                reply_markup=get_callback_btns(btns={
                'Заказать в один клик ': f'get_{car_id}',
            }),)

    else:
        await message.answer("🚫 Автомобилей в пути нет")


@user_router_manager.message(F.text.casefold().contains("автомобили в наличии"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes = message.message_id)
    await state.update_data(order_chat = message.chat.id)

    cars = await orm_get_car_by_flag(session, "В наличии")  # Получаем список машин с флагом "В наличии"
    if cars:
        for car in cars:
            car_info = (
                f"🚗 **Марка:** {car.mark}\n"
                f"📍 **Модель:** {car.model}\n"
                f"📅 **Год выпуска:** {car.year}\n"
                f"🔋 **Объём двигателя:** {car.engine_volume} л\n"
                f"👥 **Количество мест:** {car.places}\n"
                f"🏁 **Пробег:** {car.route} км\n"
                f"⛽ **Тип двигателя:** {car.engine_type}\n"
                f"🔧 **Тип коробки передач:** {car.box}\n"
                f"💰 **Стоимость:** {car.cost:,} $\n"
            )
            car_id = car.car_id
            # Отправляем фото с текстом
            await message.answer_photo(
                photo=car.foto, 
                caption=car_info, 
                parse_mode="Markdown", 
                reply_markup=get_callback_btns(btns={
                'Заказать в один клик ': f'get_{car_id}',
                
            }),)

    else:
        await message.answer("🚫 Автомобилей в пути нет")


@user_router_manager.message(F.text.casefold().contains("назад"))   # Логика Возврата в меню
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Главное меню🔙", reply_markup=main_menu.as_markup(
                            resize_keyboard=True))
    


@user_router_manager.callback_query(F.data.startswith("get_"))   # Логика Возврата в меню
async def hot_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    mesID = callback.message.message_id

    vokeb = await state.get_data()
    order_mes = vokeb.get("order_mes")
    order_chat = vokeb.get("order_chat")

    car_id = int(callback.data.split("_", 1)[1])

    car = await orm_get_car(session, car_id)

    car_info = (
                f"🚗 **Марка:** {car.mark}\n"
                f"📍 **Модель:** {car.model}\n"
                f"📅 **Год выпуска:** {car.year}\n"
                f"🔋 **Емкость батареи:** {car.engine_volume} л\n"
                f"👥 **Количество мест:** {car.places}\n"
                f"🏁 **Пробег:** {car.route} км\n"
                f"⛽ **Тип двигателя:** {car.engine_type}\n"
                f"🔧 **Тип коробки передач:** {car.box}\n"
                f"💰 **Стоимость:** {car.cost:,} $\n"
            )

    await bot.edit_message_caption(
        callback.message.chat.id,
        mesID,
       caption = f'''
Ваш заказ отправлен менеджерам на обработку
Среднее время ожидания 5-10 минут 🕝
''',
        
        
        # reply_markup=get_callback_btns(btns={
        #         'Не ждать': f'end_{order_mes}',}),
        parse_mode='HTML'
    )

    await bot.send_message(
        config.MANAGERS_GROUP_ID,
        f'''
Заказ автомобиля #️⃣{car_id}

{car_info}
''',
       parse_mode='Markdown' 
    )

    forwarded_message = await bot.forward_message(
        chat_id=config.MANAGERS_GROUP_ID, 
        from_chat_id=callback.message.chat.id, 
        message_id=order_mes
    )
    
    # Добавляем диалог в базу данных, используя ID пересланного сообщения
    await orm_add_dialog(
        session, 
        client_id=order_chat, 
        client_message_id=forwarded_message.message_id  # ID пересланного сообщения
    )









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
    await bot.send_message(chat_id=config.MANAGERS_GROUP_ID, text = "❓Вопрос от клиента")
    # Пересылаем сообщение клиента в группу менеджеров
    forwarded_message = await bot.forward_message(
        chat_id=config.MANAGERS_GROUP_ID, 
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



@user_router_manager.callback_query(StateFilter('*'), F.data.startswith("end_"))            # Обработка inline-кнопки "Завершить диалог"
async def start_handler(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:

    await callback.message.delete()
    user_id = callback.message.chat.id
    # delmes = int(callback.data.removeprefix("end_"))

    # await bot.delete_message(callback.message.chat.id, delmes)
    # Завершаем диалог
    await orm_end_dialog(session, client_id=user_id)
    await callback.message.answer("Диалог завершён!", reply_markup=main_menu.as_markup(
                            resize_keyboard=True))


@user_router_manager.message(F.text == "/end", F.reply_to_message)  # Команда /end при ответе на сообщение
async def end_dialog_with_reply(message: types.Message, session: AsyncSession) -> None:
    
    # Проверяем, что менеджер отвечает на пересланное сообщение клиента
    replied_message = message.reply_to_message

    if not replied_message or not replied_message.forward_from:
        await message.reply("❌ Эта команда должна быть ответом на пересланное сообщение клиента.")
        return

    # Получаем ID клиента из пересланного сообщения
    client_id = replied_message.forward_from.id

    # Получаем информацию о диалоге из базы данных
    dialog = await orm_get_dialog_by_client_message(session, client_message_id=replied_message.message_id)

    if not dialog:
        await message.reply("❌ Диалог не найден в базе данных.")
        return

    # Уведомляем клиента о завершении диалога
    await bot.send_message(
        chat_id=client_id,
        text="Диалог завершён менеджером. Спасибо за обращение!",
        reply_markup=main_menu.as_markup(resize_keyboard=True)
    )

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
