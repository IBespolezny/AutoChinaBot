import asyncio
import os
from traceback import format_list
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_cars, orm_get_managers, orm_get_managers_group, orm_update_calculate_column
from filters.chat_filters import ChatTypeFilter
import config

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from functions.functions import format_number, get_admins_and_managers, int_format, is_valid_phone_number
from handlers.handlers_user import Statess
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row, get_custom_callback_btns, orm_delete_car_buttons
from keybords.return_kbds import main_menu
# from keybords.inline_kbds import get_callback_btns

bot = Bot(token=os.getenv("API_TOKEN"))


#################################   Фильтр групп   #################################

user_calculate_router = Router()
user_calculate_router.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())



#######################################     Рассчитать стоимость    ###########################################

@user_calculate_router.message(F.text.casefold().contains("расчитать стоимость"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    del_mes = await message.answer("Загрузка...", reply_markup=ReplyKeyboardRemove())
    await bot.delete_message(del_mes.chat.id, del_mes.message_id)

    main_mes = await message.answer("Введите стоимость автомобиля:")
    await state.update_data(main_mes = main_mes.message_id)
    await state.set_state(Statess.enter_cost)


@user_calculate_router.message(Statess.enter_cost, F.text)
async def enter_cost(message: types.Message, state: FSMContext, session: AsyncSession):
    vokeb = await state.get_data()
    edit_mesID = int(vokeb.get("main_mes"))
    min_cost = await orm_get_calculate_column_value(session, "min_cost")
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

    if monet_for_buy < min_cost:
        await bot.edit_message_text(
        f"<b>Некорректный ввод</b>\n\nВведите сумму больше <b>{int_format(min_cost)}</b> $",
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


@user_calculate_router.callback_query(F.data.startswith("rb_"))
@user_calculate_router.callback_query(F.data.startswith("rf_"))
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


@user_calculate_router.callback_query(F.data.startswith("Гибрид_"))
@user_calculate_router.callback_query(F.data.startswith("Электрический_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    edit_mes = callback.message.message_id
    comis_rb = await orm_get_calculate_column_value(session, "comis_rb")
    bank_comis = await orm_get_calculate_column_value(session, "bank_comis")
    custom = await orm_get_calculate_column_value(session, "custom")
    delivery = await orm_get_calculate_column_value(session, "delivery")

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
            customs_cost = (cost / 100 * comis_rb) + custom  # 500 $ за таможню + 24% от цены авто
            bank_comission = cost / 100 * bank_comis  # комиссия банка
            final_cost = cost + customs_cost + delivery + bank_comission

        if vokeb.get("engine_type") == "Электрический":
            cost = int(vokeb.get("monet_for_buy"))
            customs_cost = custom  # 500 $ за таможню
            bank_comission = cost / 100 * bank_comis  # 2% комиссия банка
            final_cost = cost + customs_cost + delivery + bank_comission
        await bot.edit_message_text(
        f'''
🚗 Расчёт стоимости авто:  
__________________________

✅ Цена авто: {format_number(cost)} $  
__________________________

✅ Таможенные сборы: {int_format(customs_cost)} $  
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


@user_calculate_router.callback_query(F.data.startswith("двс_"))
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


@user_calculate_router.callback_query(F.data.startswith("новый"))
@user_calculate_router.callback_query(F.data.startswith("старый"))
async def next_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    edit_mes = callback.message.message_id

    comis_rb = await orm_get_calculate_column_value(session, "comis_rb")
    bank_comis = await orm_get_calculate_column_value(session, "bank_comis")
    custom = await orm_get_calculate_column_value(session, "custom")
    delivery = await orm_get_calculate_column_value(session, "delivery")

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
        bank_comission = cost / 100 * bank_comis  # 2% комиссия банка
        customs_cost = (cost / 100 * comis_rb) + custom  # 500 $ за таможню + 24% от цены авто
        final_cost = cost + customs_cost + delivery + bank_comission
        await bot.edit_message_text(
        f'''
🚗 Расчёт стоимости авто:  
__________________________

✅ Цена авто: {format_number(cost)} $  
__________________________

✅ Таможенные сборы: {int_format(customs_cost)} $  
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


@user_calculate_router.callback_query(F.data.startswith("1500_"))
@user_calculate_router.callback_query(F.data.startswith("1500_1800"))
@user_calculate_router.callback_query(F.data.startswith("1800_2300"))
async def next_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    edit_mes = callback.message.message_id
    engine_str_volume = callback.data
    await state.update_data(engine_str_volume = engine_str_volume)
    vokeb = await state.get_data()

    comis_rb = await orm_get_calculate_column_value(session, "comis_rb")
    bank_comis = await orm_get_calculate_column_value(session, "bank_comis")
    custom = await orm_get_calculate_column_value(session, "custom")
    delivery = await orm_get_calculate_column_value(session, "delivery")

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
    bank_comission = cost / 100 * bank_comis  # 2% комиссия банка

    if engine_volume == "1500_":
        customs_cost = await orm_get_calculate_column_value(session, "engine_volume_1500")
    elif engine_volume == "1500_1800":
        customs_cost = await orm_get_calculate_column_value(session, "engine_volume_1500_1800")
    elif engine_volume == "1800_2300":
        customs_cost = await orm_get_calculate_column_value(session, "engine_volume_1800_2300")

    final_cost = cost + customs_cost + delivery + bank_comission
    await bot.edit_message_text(
        f'''
🚗 Расчёт стоимости авто:  
__________________________

✅ Цена авто: {format_number(cost)} $  
__________________________

✅ Таможенные сборы: {int_format(customs_cost)} $  
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



@user_calculate_router.callback_query(F.data.startswith("check_"))
async def next_car(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.answer("Главное меню",reply_markup=main_menu.as_markup(
                            resize_keyboard=True))


@user_calculate_router.message(Statess.enter_phone_number, F.text)
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
