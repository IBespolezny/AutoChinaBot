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
from database.orm_query import orm_add_dialog, orm_end_dialog, orm_get_DefQuestion, orm_get_DefQuestions, orm_get_admins, orm_get_car, orm_get_car_by_flag, orm_get_cars_by_cost, orm_get_dialog_by_client_id, orm_get_dialog_by_client_message, orm_get_electrocars, orm_get_managers, orm_get_managers_group, orm_save_client_message, orm_update_manager_in_dialog
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
        chat_id= await orm_get_managers_group(session), 
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
        config.WAIT_MESSAGE, 
        reply_markup=main_menu.as_markup(
                            resize_keyboard=True),
        parse_mode='HTML'
    )
    await state.set_state(None)
















#######################################     Рассчитать стоимость    ###########################################

@user_router_manager.message(F.text.casefold().contains("расчитать стоимость"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    del_mes = await message.answer("Загрузка...", reply_markup=ReplyKeyboardRemove())
    await bot.delete_message(del_mes.chat.id, del_mes.message_id)

    main_mes = await message.answer("Введите стоимость автомобиля:")
    await state.update_data(main_mes = main_mes.message_id)
    await state.set_state(Statess.enter_cost)


@user_router_manager.message(Statess.enter_cost, F.text)
async def enter_cost(message: types.Message, state: FSMContext):
    vokeb = await state.get_data()
    edit_mesID = int(vokeb.get("main_mes"))
    try:
        monet_for_buy = float(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
        "<b>Некорректный ввод</b>\n\nВводите числа в корректном формате, например, 7900 или 8500",
        message.chat.id,
        edit_mesID,
        parse_mode='HTML',)
        return

    
    await message.delete()

    if monet_for_buy < 5000:
        await bot.edit_message_text(
        "<b>Некорректный ввод</b>\n\nВведите сумму больше 5 000 $",
        message.chat.id,
        edit_mesID,
        parse_mode='HTML',
    )
        return
        
    await state.update_data(monet_for_buy = monet_for_buy)

    await bot.edit_message_text(
        "Выберите регион:",
        message.chat.id,
        edit_mesID,
        reply_markup=get_custom_callback_btns(btns={
            '🇧🇾 РБ':'rb_',
            '🇷🇺 РФ':'rf_',
            }, layout=[2]), 
    )
    await state.set_state(None)


@user_router_manager.callback_query(F.data.startswith("rb_"))
@user_router_manager.callback_query(F.data.startswith("rf_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    edit_mes = callback.message.message_id
    region = callback.data.replace("_", "")
    await state.update_data(region = region)

    await bot.edit_message_text(
        "Выберите тип двигателя:",
        callback.message.chat.id,
        edit_mes,
        reply_markup=get_custom_callback_btns(btns={
            'ДВС':'двс_',
            'Гибрид':'Гибрид_',
            'Электрический':'Электрический_',
            }, layout=[2,1])
    )


@user_router_manager.callback_query(F.data.startswith("Гибрид_"))
@user_router_manager.callback_query(F.data.startswith("Электрический_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    edit_mes = callback.message.message_id
    await bot.edit_message_text(
        "Идёт расчёт...",
        callback.message.chat.id,
        edit_mes,
    )
    await asyncio.sleep(2)

    engine_type = callback.data.replace("_", "")
    await state.update_data(engine_type = engine_type)
    vokeb = await state.get_data()

    if vokeb.get("region") == "rb":
        if vokeb.get("engine_type") == "Гибрид":
            cost = int(vokeb.get("monet_for_buy"))
            customs_cost = (cost / 100 * 24) + 500  # 500 $ за таможню + 24% от цены авто
            delivery = 2300
            bank_comission = cost / 100 * 2  # 2% комиссия банка
            final_cost = cost + customs_cost + delivery + bank_comission

        if vokeb.get("engine_type") == "Электрический":
            cost = int(vokeb.get("monet_for_buy"))
            customs_cost = 500  # 500 $ за таможню
            delivery = 2300
            bank_comission = cost / 100 * 2  # 2% комиссия банка
            final_cost = cost + customs_cost + delivery + bank_comission
        await bot.edit_message_text(
        f'''
🚗 Расчёт стоимости авто:  
__________________________

✅ Цена авто: {format_number(cost)} $  
__________________________

✅ Таможенные сборы: {format_number(customs_cost)} $  
__________________________

✅ Доставка до Минска: {format_number(int(delivery))} $  
__________________________

✅ Банковская комиссия: {format_number(bank_comission)} $  
__________________________

🟢 Приблизительная стоимость: \n➡️ {format_number(int(final_cost))} $
''',
        callback.message.chat.id,
        edit_mes,
        reply_markup=get_custom_callback_btns(btns={
            'Главное меню':'check_',
            }, layout=[1])
    )
    
    elif vokeb.get("region") == "rf":
        await bot.edit_message_text(
            "Оставьте свой номер, чтобы мы могли с вами связаться",
            callback.message.chat.id,
            edit_mes
        )
        await state.set_state(Statess.enter_phone_number)


@user_router_manager.callback_query(F.data.startswith("двс_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    edit_mes = callback.message.message_id
    engine_type = callback.data.replace("_", "")
    await state.update_data(engine_type = engine_type)
    
    await bot.edit_message_text(
        "Выберите тип автомобиля:",
        callback.message.chat.id,
        edit_mes,
        reply_markup=get_custom_callback_btns(btns={
            'до 3-х лет':'новый',
            '3-5 лет':'старый',
            }, layout=[2])
    )


@user_router_manager.callback_query(F.data.startswith("новый"))
@user_router_manager.callback_query(F.data.startswith("старый"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    edit_mes = callback.message.message_id

    edge_type = callback.data
    await state.update_data(edge_type = edge_type)
    vokeb = await state.get_data()

    if edge_type == "новый":
        if vokeb.get("region") == "rf":
            await bot.edit_message_text(
            "Оставьте свой номер, чтобы мы могли с вами связаться",
            callback.message.chat.id,
            edit_mes
        )
            await state.set_state(Statess.enter_phone_number)
            return

        await bot.edit_message_text(
        "Идёт расчёт...",
        callback.message.chat.id,
        edit_mes,
    )
        await asyncio.sleep(2)

        cost = int(vokeb.get("monet_for_buy"))
        delivery = 2300
        bank_comission = cost / 100 * 2  # 2% комиссия банка
        customs_cost = (cost / 100 * 24) + 500  # 500 $ за таможню + 24% от цены авто
        final_cost = cost + customs_cost + delivery + bank_comission
        await bot.edit_message_text(
        f'''
🚗 Расчёт стоимости авто:  
__________________________

✅ Цена авто: {format_number(cost)} $  
__________________________

✅ Таможенные сборы: {format_number(customs_cost)} $  
__________________________

✅ Доставка до Минска: {format_number(int(delivery))} $  
__________________________

✅ Банковская комиссия: {format_number(bank_comission)} $  
__________________________

🟢 Приблизительная стоимость: \n➡️ {format_number(int(final_cost))} $
''',
        callback.message.chat.id,
        edit_mes,
        reply_markup=get_custom_callback_btns(btns={
            'Главное меню':'check_',
            }, layout=[1])
    )

    elif edge_type == "старый":
        await bot.edit_message_text(
        "Выберите объём двигателя:",
        callback.message.chat.id,
        edit_mes,
        reply_markup=get_custom_callback_btns(btns={
            'до 1500':'1500_',
            '1500-1800':'1500_1800',
            '1800-2300':'1800_2300',
            }, layout=[1,2])
    )


@user_router_manager.callback_query(F.data.startswith("1500_"))
@user_router_manager.callback_query(F.data.startswith("1500_1800"))
@user_router_manager.callback_query(F.data.startswith("1800_2300"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    edit_mes = callback.message.message_id
    engine_str_volume = callback.data
    await state.update_data(engine_str_volume = engine_str_volume)
    vokeb = await state.get_data()

    if vokeb.get("region") == "rf":
        await bot.edit_message_text(
            "Оставьте свой номер, чтобы мы могли с вами связаться",
            callback.message.chat.id,
            edit_mes
        )
        await state.set_state(Statess.enter_phone_number)
        return
    
    await bot.edit_message_text(
        "Идёт расчёт...",
        callback.message.chat.id,
        edit_mes,
    )
    await asyncio.sleep(2)

    engine_volume = callback.data
    await state.update_data(engine_volume = engine_volume)
    cost = int(vokeb.get("monet_for_buy"))
    delivery = 2300
    bank_comission = cost / 100 * 2  # 2% комиссия банка

    if engine_volume == "1500_":
        customs_cost = 1750
    elif engine_volume == "1500_1800":
        customs_cost = 3000
    elif engine_volume == "1800_2300":
        customs_cost = 3800

    final_cost = cost + customs_cost + delivery + bank_comission
    await bot.edit_message_text(
        f'''
🚗 Расчёт стоимости авто:  
__________________________

✅ Цена авто: {format_number(cost)} $  
__________________________

✅ Таможенные сборы: {format_number(customs_cost)} $  
__________________________

✅ Доставка до Минска: {format_number(int(delivery))} $  
__________________________

✅ Банковская комиссия: {format_number(bank_comission)} $  
__________________________

🟢 Приблизительная стоимость: \n➡️ {format_number(int(final_cost))} $
''',
        callback.message.chat.id,
        edit_mes,
        reply_markup=get_custom_callback_btns(btns={
            'Главное меню':'check_',
            }, layout=[1])
    )



@user_router_manager.callback_query(F.data.startswith("check_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.answer("Главное меню",reply_markup=main_menu.as_markup(
                            resize_keyboard=True))


@user_router_manager.message(Statess.enter_phone_number, F.text)
async def enter_cost(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()

    # Получаем сохранённые данные
    vokeb = await state.get_data()
    edit_mesID = int(vokeb.get("main_mes"))
    phone_number = message.text

    # Проверяем, соответствует ли номер международному формату
    if not is_valid_phone_number(phone_number):
        await bot.edit_message_text(f"❌ Неверный формат номера\n<b>{phone_number}</b>\nВведите номер в международном формате, например: +1234567890", message.chat.id, edit_mesID, parse_mode='HTML')
        return  # Выходим из функции, если номер неверный

    cost = int(vokeb.get("monet_for_buy"))
    engine_type = vokeb.get("engine_type")

    send_text = f'''
<b>Запрос цены от клиента</b>💸

Цена: {format_number(cost)} $
Тип двигателя: {engine_type}

Имя пользоватлея: @{message.from_user.username}
Телефон: {phone_number}
'''

    if vokeb.get("engine_str_volume"):
        engine_volume = vokeb.get("engine_str_volume")
        edge_type = vokeb.get("edge_type")
        send_text = f'''
<b>Запрос цены от клиента</b>💸

Цена: {format_number(cost)} $
Тип двигателя: {engine_type}
Тип авто: {edge_type}
Объём двигателя: {engine_volume}

Имя пользоватлея: @{message.from_user.username}
Телефон: {phone_number}

'''


    await bot.edit_message_text(
        "Ваш запрос отправлен менеджеру.\nОжидайте, с вами свяжутся🕐",
        message.chat.id,
        edit_mesID,
        reply_markup=get_custom_callback_btns(btns={
            'Главное меню':'check_',
            }, layout=[1])
    )

    await bot.send_message(
        await orm_get_managers_group(session),
        send_text,
parse_mode='HTML',
    )
    await state.set_state(None)
















#######################################     Горячие предложения    ###########################################

@user_router_manager.message(F.text.casefold().contains("горячие предложения🔥"))   # Логика Горячие предложения
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("🚗Выберите тип автомобиля", reply_markup=hot_menu.as_markup(
                            resize_keyboard=True))
    

    
@user_router_manager.message(F.text.casefold().contains("по стоимости"))
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
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
    
    cars = await orm_get_car_by_flag(session, "популярные")
    if cars:
        total_cars = len(cars)
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        car_id = car.car_id
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"
                
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            
            if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        else:
            # Если значение `electrocar` некорректное
            car_info = "❌ Ошибка: Неправильное значение поля electrocar!"
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '◀️ Предыдущее': f'left',
                'Следующее ▶️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            }
        
        send_message = await message.answer_photo(
            photo=car.photo,
            caption=car_info,
            reply_markup=get_callback_btns(btns=btns),
        )
        await state.update_data(send_message=send_message.message_id)
    else:
        send_message = await message.answer("🚫 Популярные автомобили не найдены.")
        await state.update_data(send_message=send_message.message_id)
    

@user_router_manager.message(F.text.casefold().contains("электроавтомобили"))
async def hot_handler(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await state.update_data(order_mes=message.message_id, order_chat=message.chat.id)
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
    
    cars = await orm_get_electrocars(session)
    if cars:
        total_cars = len(cars)
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        car_id = car.car_id

        car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
        # Если это админ или менеджер — добавляем номер авто
        if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"


        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '◀️ Предыдущее': f'left',
                'Следующее ▶️': f'right',
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
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
    
    cars = await orm_get_car_by_flag(session, "в пути")
    if cars:
        total_cars = len(cars)
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        car_id = car.car_id
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {car.power_bank} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"
                
        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            # Если это админ или менеджер — добавляем номер авто
            if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        else:
            # Если значение `electrocar` некорректное
            car_info = "❌ Ошибка: Неправильное значение поля electrocar!"
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '◀️ Предыдущее': f'left',
                'Следующее ▶️': f'right',
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
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
    vokeb = await state.get_data()
    del_mes = vokeb.get("send_message")
    if del_mes:
        await bot.delete_message(message.chat.id, del_mes)
        
    cars = await orm_get_car_by_flag(session, "в наличии")
    if cars:
        total_cars = len(cars)
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        car_id = car.car_id
        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)}

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)}

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            # Если это админ или менеджер — добавляем номер авто
            if message.from_user.id in admins_ids or message.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        else:
            # Если значение `electrocar` некорректное
            car_info = "❌ Ошибка: Неправильное значение поля electrocar!"
        
        
        # Определяем кнопки в зависимости от количества автомобилей
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '◀️ Предыдущее': f'left',
                'Следующее ▶️': f'right',
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
async def next_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
    data = await state.get_data()
    cars = data.get("cars_list", [])
    index = data.get("current_index", 0)
    message_id = data.get("send_message")
    chat_id = data.get("order_chat")
    
    if cars:
        total_cars = len(cars)
        index = (index + 1) % len(cars)
        await state.update_data(current_index=index)
        car = cars[index]
        car_id = car.car_id

        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            if callback.from_user.id in admins_ids or callback.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            # Если это админ или менеджер — добавляем номер авто
            if callback.from_user.id in admins_ids or callback.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        else:
            # Если значение `electrocar` некорректное
            car_info = "❌ Ошибка: Неправильное значение поля electrocar!"

        await callback.bot.edit_message_media(
            media=types.InputMediaPhoto(media=car.photo, caption=car_info, parse_mode="Markdown"),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=get_callback_btns(btns = {
                '◀️ Предыдущее': f'left',
                'Следующее ▶️': f'right',
                'Заказать в один клик': f'get_{car_id}',
            })
        )
    await callback.answer()


@user_router_manager.callback_query(F.data.startswith("left"))
async def prev_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)
    data = await state.get_data()
    cars = data.get("cars_list", [])
    index = data.get("current_index", 0)
    message_id = data.get("send_message")
    chat_id = data.get("order_chat")
    
    if cars:
        total_cars = len(cars)
        index = (index - 1) % len(cars)
        await state.update_data(current_index=index)
        car = cars[index]
        car_id = car.car_id

        if car.electrocar == "yes":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            if callback.from_user.id in admins_ids or callback.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        elif car.electrocar == "no":
            car_info = (
            f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
'''
        )
            # Если это админ или менеджер — добавляем номер авто
            if callback.from_user.id in admins_ids or callback.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        else:
            # Если значение `electrocar` некорректное
            car_info = "❌ Ошибка: Неправильное значение поля electrocar!"

        await callback.bot.edit_message_media(
            media=types.InputMediaPhoto(media=car.photo, caption=car_info, parse_mode="Markdown"),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=get_callback_btns(btns = {
                '◀️ Предыдущее': f'left',
                'Следующее ▶️': f'right',
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

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
'''                       
            )
        
    if car.electrocar == "no":
        car_info = (f'''
{car.mark} {car.model} {car.package}, {car.year} год

💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
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
        await orm_get_managers_group(session),
        f'''
Заказ автомобиля #️⃣{car_id}
{car_info}

⬇️Ссылка на клиента⬇️
''',
       parse_mode='HTML' 
    )

    forwarded_message = await bot.forward_message(
        chat_id=await orm_get_managers_group(session), 
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

    # Проверяем, есть ли сообщение для удаления
    if del_mes:
        await bot.delete_message(callback.message.chat.id, del_mes)

    # Получаем админов и менеджеров
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)

    # Разбираем диапазон стоимости
    min_val, max_val = map(float, car_cost.split('_'))
    cars = await orm_get_cars_by_cost(session, min_val, max_val)  # только популярные

    if cars:
        total_cars = len(cars)
        await state.update_data(cars_list=cars, current_index=0)
        car = cars[0]
        car_id = car.car_id

        # Проверяем, является ли авто электрокаром
        if car.electrocar.lower() == "yes":  # исправил на lower(), чтобы учитывать разные написания
            car_info = (
                f'''
{car.mark} {car.model} {car.package}, {car.year} год
💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Запас хода: {int_format(car.power_reserve)} км
✅ Батарея: {int_format(car.power_bank)} кВтч
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
''')

            # Если это админ или менеджер — добавляем номер авто
            if callback.from_user.id in admins_ids or callback.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        elif car.electrocar.lower() == "no":
            car_info = (
                f'''
{car.mark} {car.model} {car.package}, {car.year} год
💰 Цена: ${int_format(car.cost)} с учетом доставки (40-60 дней)

✅ Пробег: {int_format(car.route)} км
✅ Тип топлива: {car.engine_type} 
✅ Объём двигателя: {car.engine_volume} л
✅ Мощность: {int_format(car.power)} л.с.
✅ Привод: {car.weel_drive}
✅ Кузов: {car.body}
\n🔢 Найдено автомобилей: {total_cars}
''')

            # Если это админ или менеджер — добавляем номер авто
            if callback.from_user.id in admins_ids or callback.from_user.id in managers_ids:
                car_info += f"#️⃣{car_id} номер авто"

        else:
            # Если значение `electrocar` некорректное
            car_info = "❌ Ошибка: Неправильное значение поля electrocar!"

        # Создаем кнопки
        btns = {'Заказать в один клик': f'get_{car_id}'}
        if len(cars) > 1:
            btns = {
                '◀️ Предыдущее': 'left',
                'Следующее ▶️': 'right',
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
