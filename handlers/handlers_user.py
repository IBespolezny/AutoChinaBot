import asyncio
import re
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, Message, InlineKeyboardMarkup, InlineKeyboardButton
import requests

import config
from database.orm_query import orm_add_dialog, orm_end_dialog, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_car, orm_get_car_by_flag, orm_get_cars_by_cost, orm_get_dialog_by_client_message, orm_get_electrocars, orm_get_managers, orm_save_client_message, orm_update_manager_in_dialog
from database.models import Dialog
from filters.chat_filters import ChatTypeFilter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# from keybords.inline_kbds import get_callback_btns
from functions.functions import format_number
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row
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

    Mark = State()                              # Добавление марки авто
    Model = State()                              # Добавление модели авто
    Year = State()                              # Добавление года авто
    engine = State()                              # Добавление года авто
    engine_volume = State()                              # Добавление года авто
    route = State()                              # Добавление года авто
    engine_type = State()                              # Добавление года авто
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


@user_router_manager.message(F.text.casefold().contains("назад"))  # Обработка кнопки "назад"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    await message.answer("Главное меню🔙", reply_markup=main_menu.as_markup(
                            resize_keyboard=True))

#######################################     Подобрать автомобиль    ###########################################

@user_router_manager.message(F.text.casefold().contains("подобрать автомобиль"))   # Логика Подобрать автомобиль
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите регион:", reply_markup=region_menu.as_markup(
                            resize_keyboard=True))
    await state.set_state(Statess.help_buy_auto)
    


@user_router_manager.message(Statess.help_buy_auto, F.text.casefold().contains("рф"))
@user_router_manager.message(Statess.help_buy_auto, F.text.casefold().contains("рб"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    region = message.text
    await state.update_data(region = region)
    await message.answer("Выберите тип двигателя:", reply_markup=engine_menu.as_markup(
                            resize_keyboard=True))


@user_router_manager.message(Statess.help_buy_auto, F.text.casefold().contains("двс"))
@user_router_manager.message(Statess.help_buy_auto, F.text.casefold().contains("электрический"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    engine_type = message.text
    await state.update_data(engine_type = engine_type)
    await message.answer("Выберите тип автомобиля:", reply_markup=old_or_new_menu.as_markup(
                            resize_keyboard=True))


@user_router_manager.message(Statess.help_buy_auto, F.text.casefold().contains("новый"))
@user_router_manager.message(Statess.help_buy_auto, F.text.casefold().contains("б/у"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    edge_type = message.text
    await state.update_data(edge_type = edge_type)
    vokeb = await state.get_data()

    mesID = message.message_id  # ID исходного сообщения клиента
    delmes = await message.answer("Поиск свободного менеджера...")

    await bot.send_message(
        chat_id=config.MANAGERS_GROUP_ID, 
        text = f'''
Подбор автомобиля 🚗

<b>Регион:</b> {vokeb.get("region")}
<b>Тип двигателя:</b> {vokeb.get("engine_type")}
<b>Тип автомобиля:</b> {vokeb.get("edge_type")}

⬇️Ссылка на клиента⬇️
''',
parse_mode='HTML'
        )
    
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
        config.WAIT_MESSAGE, 
        reply_markup=main_menu.as_markup(
                            resize_keyboard=True),
        parse_mode='HTML'
    )
    await state.set_state(None)
















#######################################     Рассчитать стоимость    ###########################################

@user_router_manager.message(F.text.casefold().contains("расчитать стоимость"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    main_mes = await message.answer("Введите свой бюджет на покупку:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.enter_cost)


@user_router_manager.message(Statess.enter_cost, F.text.casefold().contains("рб"))   # Логика Расчитать стоимость автомобиля
@user_router_manager.message(Statess.enter_cost, F.text.casefold().contains("рф"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    vokeb = await state.get_data()
    money = float(vokeb.get("monet_for_buy", 0))

    if message.text.casefold().__contains__("рб"):
        edit_mes = await message.answer("Идёт расчёт...")
        del_mes = await message.answer("Подготовка", reply_markup=ReplyKeyboardRemove())
        await del_mes.delete()

        procent = money / 100 * 24   # 24 процента от цены клиента
        cost_with = money + procent  # цена с учётом таможни
        final_cost = cost_with + 120 + 566 + 200 + 380 + 180 + 70
        
        await asyncio.sleep(2)
        await bot.edit_message_text(
        f"Стоимость выбранного автомобиля: \n{format_number(final_cost)} $",
        message.chat.id,
        edit_mes.message_id,
        reply_markup=get_callback_btns(btns={
            'Продолжить ✔️':'check_',
        })
        )
        
        
    elif message.text.casefold().__contains__("рф"):

        edit_mes = await message.answer("Идёт расчёт...")
        del_mes = await message.answer("Подготовка", reply_markup=ReplyKeyboardRemove())
        await del_mes.delete()

        procent = money / 100 * 48   # 48 процента от цены клиента
        cost_with = money + procent  # цена с учётом таможни
        final_cost = cost_with + 1250  # добавочная стоимость
        await asyncio.sleep(2)
        await bot.edit_message_text(
        f"Стоимость выбранного автомобиля: \n{format_number(final_cost)} $",
        message.chat.id,
        edit_mes.message_id,
        reply_markup=get_callback_btns(btns={
            'Продолжить ✔️':'check_',
        })
        )

    await state.set_state(None)


@user_router_manager.message(Statess.enter_cost, F.text)
async def enter_cost(message: types.Message, state: FSMContext):
    monet_for_buy = float(message.text)
    await state.update_data(monet_for_buy = monet_for_buy)

    await message.answer(
        "Выберите регион:",
        reply_markup=region_menu.as_markup(
                            resize_keyboard=True),
    )


@user_router_manager.callback_query(F.data.startswith("check_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.answer("Главное меню",reply_markup=main_menu.as_markup(
                            resize_keyboard=True))



















#######################################     Горячие предложения    ###########################################

@user_router_manager.message(F.text.casefold().contains("горячие предложения🔥"))   # Логика Горячие предложения
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("🚗Выберите тип автомобиля", reply_markup=hot_menu.as_markup(
                            resize_keyboard=True))
    

    
@user_router_manager.message(F.text.casefold().contains("подборка автомобилей по стоимости"))
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(order_mes=message.message_id, order_chat=message.chat.id)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)

    send_message = await message.answer("Выберите стоимость автомобиля", reply_markup=get_callback_btns(btns={
                'до 15 $$$': f'0_15000',
                '15 - 20 $$$': f'15000_20000',
                '20 - 30 $$$': f'20000_30000',
                '30+ $$$': f'30000_1000000',
            }),)
    await state.update_data(send_message = send_message.message_id)



@user_router_manager.message(F.text.casefold().contains("популярные автомобили"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes=message.message_id, order_chat=message.chat.id)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
    
    cars = await orm_get_car_by_flag(session, "популярные")
    if cars:
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        car_id = car.car_id
        
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            }
        
        send_message = await message.answer_photo(
            photo=car.photo,
            caption=car_info,
            parse_mode="Markdown",
            reply_markup=get_callback_btns(btns=btns),
        )
        await state.update_data(send_message=send_message.message_id)
    else:
        send_message = await message.answer("🚫 Популярные автомобили не найдены.")
        await state.update_data(send_message=send_message.message_id)
    

@user_router_manager.message(F.text.casefold().contains("электроавтомобили"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes=message.message_id, order_chat=message.chat.id)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
    
    cars = await orm_get_electrocars(session)
    if cars:
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]

        car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )

        car_id = car.car_id

        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            }

        send_message = await message.answer_photo(
            photo=car.photo,
            caption=car_info,
            parse_mode="Markdown",
            reply_markup=get_callback_btns(btns=btns),
        )
        await state.update_data(send_message=send_message.message_id)
    else:
        send_message = await message.answer("🚫 Электроавтомобили в пути не найдены.")
        await state.update_data(send_message=send_message.message_id)


@user_router_manager.message(F.text.casefold().contains("автомобили в пути"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes=message.message_id, order_chat=message.chat.id)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
    
    cars = await orm_get_car_by_flag(session, "в пути")
    if cars:
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        car_id = car.car_id
        
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            }
        
        send_message = await message.answer_photo(
            photo=car.photo,
            caption=car_info,
            parse_mode="Markdown",
            reply_markup=get_callback_btns(btns=btns),
        )
        await state.update_data(send_message=send_message.message_id)
    else:
        send_message = await message.answer("🚫 Автомобили в пути не найдены.")
        await state.update_data(send_message=send_message.message_id)


@user_router_manager.message(F.text.casefold().contains("автомобили в наличии"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes=message.message_id, order_chat=message.chat.id)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
        
    cars = await orm_get_car_by_flag(session, "в наличии")
    if cars:
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        car_id = car.car_id
        
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            }

        send_message = await message.answer_photo(
            photo=car.photo,
            caption=car_info,
            parse_mode="Markdown",
            reply_markup=get_callback_btns(btns=btns),
        )
        await state.update_data(send_message=send_message.message_id)
    else:
        send_message = await message.answer("🚫 Автомобили в наличии не найдены.")
        await state.update_data(send_message=send_message.message_id)
    






@user_router_manager.callback_query(F.data.startswith("right"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cars = data.get("cars_list", [])
    index = data.get("current_index", 0)
    message_id = data.get("send_message")
    chat_id = data.get("order_chat")
    
    if cars:
        index = (index + 1) % len(cars)
        await state.update_data(current_index=index)
        car = cars[index]
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        car_id = car.car_id
        await callback.bot.edit_message_media(
            media=types.InputMediaPhoto(media=car.photo, caption=car_info, parse_mode="Markdown"),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=get_callback_btns(btns={
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            })
        )
    await callback.answer()


@user_router_manager.callback_query(F.data.startswith("left"))
async def prev_car(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cars = data.get("cars_list", [])
    index = data.get("current_index", 0)
    message_id = data.get("send_message")
    chat_id = data.get("order_chat")
    
    if cars:
        index = (index - 1) % len(cars)
        await state.update_data(current_index=index)
        car = cars[index]
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        car_id = car.car_id
        await callback.bot.edit_message_media(
            media=types.InputMediaPhoto(media=car.photo, caption=car_info, parse_mode="Markdown"),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=get_callback_btns(btns={
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            })
        )
    await callback.answer()



@user_router_manager.callback_query(F.data.startswith("get_"))   # Логика Возврата в меню
async def hot_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    mesID = callback.message.message_id

    vokeb = await state.get_data()
    order_mes = vokeb.get("order_mes")
    order_chat = vokeb.get("order_chat")

    car_id = int(callback.data.split("_", 1)[1])

    car = await orm_get_car(session, car_id)
    if car.electrocar == "yes":
        car_info = (f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
'''                       
            )
        
    if car.electrocar == "no":
        car_info = (f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
'''                       
            )

    await bot.edit_message_caption(
        callback.message.chat.id,
        mesID,
        caption = f'''
Ваш заказ отправлен менеджерам на обработку
Среднее время ожидания 5-10 минут 🕝
''', 
        parse_mode='HTML'
    )

    await bot.send_message(
        config.MANAGERS_GROUP_ID,
        f'''
Заказ автомобиля #️⃣{car_id}
{car_info}

⬇️Ссылка на клиента⬇️
''',
       parse_mode='HTML' 
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


@user_router_manager.callback_query(F.data.startswith("0_15000"))
@user_router_manager.callback_query(F.data.startswith("15000_20000"))
@user_router_manager.callback_query(F.data.startswith("20000_30000"))
@user_router_manager.callback_query(F.data.startswith("30000_1000000"))
async def prev_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    car_cost = callback.data
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    await bot.delete_message(callback.message.chat.id, del_mes)

    min_val, max_val = map(float, car_cost.split('_'))

    cars = await orm_get_cars_by_cost(session, min_val, max_val)
    print(cars)
    if cars:
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Запас хода: {format_number(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${format_number(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {format_number(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {car.power} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}

'''
        )
        car_id = car.car_id
        
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '⬅️': f'left',
                '➡️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            }
        
        send_message = await callback.message.answer_photo(
            photo=car.photo,
            caption=car_info,
            parse_mode="HTML",
            reply_markup=get_callback_btns(btns=btns),
        )
        await state.update_data(send_message=send_message.message_id)
    else:
        send_message = await callback.message.answer("🚫 Автомобили такой ценовой категории не найдены")
        await state.update_data(send_message=send_message.message_id)
    





















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
    await bot.send_message(chat_id=config.MANAGERS_GROUP_ID, text = "❓Вопрос от клиента\n\n⬇️Ссылка на клиента⬇️")
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
