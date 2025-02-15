import asyncio
import os
from traceback import format_list
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_dialog, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_car, orm_get_car_by_flag, orm_get_cars, orm_get_cars_by_cost, orm_get_electrocars, orm_get_managers, orm_get_managers_group, orm_update_calculate_column
from filters.chat_filters import ChatTypeFilter
import config

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from functions.functions import format_number, get_admins_and_managers, int_format, is_valid_phone_number
from handlers.handlers_user import Statess
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row, get_custom_callback_btns, orm_delete_car_buttons
from keybords.return_kbds import main_menu, hot_menu
# from keybords.inline_kbds import get_callback_btns

bot = Bot(token=os.getenv("API_TOKEN"))


#################################   Фильтр групп   #################################

user_find_auto = Router()
user_find_auto.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())



#######################################     Горячие предложения    ###########################################

@user_find_auto.message(F.text.casefold().contains("горячие предложения🔥"))   # Логика Горячие предложения
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("🚗Выберите тип автомобиля", reply_markup=hot_menu.as_markup(
                            resize_keyboard=True))
    

    
@user_find_auto.message(F.text.casefold().contains("по стоимости"))
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



@user_find_auto.message(F.text.casefold().contains("популярные автомобили"))
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
    

@user_find_auto.message(F.text.casefold().contains("электроавтомобили"))
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


@user_find_auto.message(F.text.casefold().contains("автомобили в пути"))
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


@user_find_auto.message(F.text.casefold().contains("автомобили в наличии"))
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
    






@user_find_auto.callback_query(F.data.startswith("right"))
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


@user_find_auto.callback_query(F.data.startswith("left"))
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



@user_find_auto.callback_query(F.data.startswith("get_"))   # Логика Возврата в меню
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


@user_find_auto.callback_query(F.data.startswith("0_15000"))
@user_find_auto.callback_query(F.data.startswith("15000_20000"))
@user_find_auto.callback_query(F.data.startswith("20000_30000"))
@user_find_auto.callback_query(F.data.startswith("30000_1000000"))
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
