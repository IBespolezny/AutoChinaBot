import asyncio
import os
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_car, orm_get_cars, orm_get_managers, orm_update_calculate_column, update_car_field
from filters.chat_filters import ChatTypeFilter
import config

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from functions.functions import get_admins_and_managers, int_format
from handlers.handlers_user import Statess
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row, get_custom_callback_btns, orm_delete_car_buttons
from keybords.return_kbds import admin_menu, access_settings, admin_settings, manager_settings, auto_settings, add_del_back_menu
# from keybords.inline_kbds import get_callback_btns

bot = Bot(token=os.getenv("API_TOKEN"))


#################################   Фильтр групп   #################################

admin_edit_cars = Router()
admin_edit_cars.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())


################################ Редактировать автомобиль ###########################

@admin_edit_cars.message(Statess.Admin_kbd, F.text.casefold().contains("редактировать автомобиль"))
async def show_car_list(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    await message.delete()


    cars = await orm_get_cars(session)
    if not cars:
        await message.answer("❌ В базе нет авто для редактирования")
        return
    if cars:
        btns = {f"{car_mark} {car_model} {int(car_cost)}": f"update_car_{car_id}" for car_id, car_mark, car_model, car_cost in cars}
        btns["Назад"] = "bback_"

    edit_mes = await message.answer(
        "Выберите автомобиль для редактирования:",
reply_markup=get_callback_btns_single_row(btns=btns),
parse_mode='HTML'
    )
    await state.update_data(edit_mes_id = edit_mes.message_id)


@admin_edit_cars.callback_query(F.data.startswith("update_car_"))
async def delete_selected_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()
    car_id = int(callback.data.split("_")[2])  # Получаем ID автомобиля из callback_data
    vokeb = await state.get_data()
    edit_mes_id = vokeb.get("edit_mes_id")
    edit_car = await orm_get_car(session, car_id)

    if edit_car.electrocar == "yes":
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Запас хода: {int_format(edit_car.power_reserve)} км
✅ Батарея: {int_format(edit_car.power_bank)} кВтч
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''     
        btns={
                "Цена": "edit_cost",
                "Флаг": "edit_flag",
                "Пробег": "edit_route",
                "Запас хода": "edit_power_reserve",
                "Батарея": "edit_power_bank",
                "Привод": "edit_weel_drive",
                "Кузов": "edit_body",
                "Фото": "edit_photo",
                "Назад": "back_to_car_list",
            }
        layout=[2, 2, 2, 2, 1]


        
    elif edit_car.electrocar == "no":
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Тип топлива: {edit_car.engine_type} 
✅ Объём двигателя: {edit_car.engine_volume} л
✅ Мощность: {int_format(edit_car.power)} л.с.
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
            "Цена":"edit_cost",
            "Флаг":"edit_flag",
            "Пробег":"edit_route",
            "Тип топлива":"edit_engine_type",
            "Объём двигателя":"edit_engine_volume",
            "Мощность":"edit_power",
            "Привод":"edit_weel_drive",
            "Кузов":"edit_body",
            "Фото":"edit_photo",
            "Назад":"back_to_car_list",
        }
        layout=[2, 2, 2, 2, 1, 1]
        
    del_mes = await bot.send_photo(
        callback.message.chat.id,
        edit_car.photo,
        caption=send_text,
        reply_markup=get_custom_callback_btns(btns=btns, layout=layout
        )
    )
    await state.update_data(del_mes_id = del_mes.message_id)
    await state.update_data(car_id = car_id)






####################### Проверка без выбора #####################

@admin_edit_cars.callback_query(F.data.startswith("edit_cost"))
@admin_edit_cars.callback_query(F.data.startswith("edit_route"))
@admin_edit_cars.callback_query(F.data.startswith("edit_engine_volume"))
@admin_edit_cars.callback_query(F.data.startswith("edit_power_reserve")) # Электрокар
@admin_edit_cars.callback_query(F.data.startswith("edit_power_bank")) # Электрокар
async def edit_car_param(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Обработчик выбора параметра для изменения."""
    await callback.message.delete()
    
    param_mapping = {
        "cost": "цены",
        "route": "пробега",
        "engine_volume": "объёма двигателя",
        "power_reserve": "запаса хода",
        "power_bank": "батареи"
    }

    param_key = callback.data.replace("edit_", "")
    edit_param = param_mapping.get(param_key, param_key)  # Получаем название параметра для отображения

    await state.update_data(edit_param=param_key) 

    # Получаем ID автомобиля из state
    data = await state.get_data()
    car_id = data.get("car_id")
    
    edit_mes = await callback.message.answer(f"Введите новое значение {edit_param}:", reply_markup=get_callback_btns_single_row(btns={"Назад":f"back_to_car_{car_id}"}))
    await state.set_state(Statess.Edit_car_int)
    await state.update_data(edit_mes_id = edit_mes.message_id)

    


@admin_edit_cars.message(Statess.Edit_car_int, F.text)
async def save_car_param(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    """Сохраняет новое значение в БД."""
    await message.delete()
    data = await state.get_data()
    car_id = data.get("car_id")
    edit_mes_id = int(data.get("edit_mes_id"))
    edit_param = data.get("edit_param")

    try:
        new_value = float(message.text.replace(",", "."))

    
    except ValueError:
        await bot.edit_message_text(
            f"❌ Неккоректное значение\n<b>{message.text}</b>\n\nВведите численное значение, например, 123 или 123,12",
            message.chat.id,
            edit_mes_id,
            reply_markup=get_callback_btns_single_row(btns={"Назад":f"back_to_car_{car_id}"}),
            parse_mode='HTML'
        )
        return

    if new_value < 0:
        await bot.edit_message_text(
            f"❌ Неккоректное значение\n<b>{new_value}</b>\n\nВведите сумму больше 0",
            message.chat.id,
            edit_mes_id,
            reply_markup=get_callback_btns_single_row(btns={"Назад":f"back_to_car_{car_id}"}),
            parse_mode='HTML'
        )
        return
    await update_car_field(session, car_id, edit_param, new_value)

    edit_car = await orm_get_car(session, car_id)
    if edit_car.electrocar == "yes":
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Запас хода: {int_format(edit_car.power_reserve)} км
✅ Батарея: {int_format(edit_car.power_bank)} кВтч
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
                "Цена": "edit_cost",
                "Флаг": "edit_flag",
                "Пробег": "edit_route",
                "Запас хода": "edit_power_reserve",
                "Батарея": "edit_power_bank",
                "Привод": "edit_weel_drive",
                "Кузов": "edit_body",
                "Фото": "edit_photo",
                "Назад": "back_to_car_list",
            }
        layout=[2, 2, 2, 2, 1]

    else:
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Тип топлива: {edit_car.engine_type} 
✅ Объём двигателя: {edit_car.engine_volume} л
✅ Мощность: {int_format(edit_car.power)} л.с.
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
            "Цена":"edit_cost",
            "Флаг":"edit_flag",
            "Пробег":"edit_route",
            "Тип топлива":"edit_engine_type",
            "Объём двигателя":"edit_engine_volume",
            "Мощность":"edit_power",
            "Привод":"edit_weel_drive",
            "Кузов":"edit_body",
            "Фото":"edit_photo",
            "Назад":"back_to_car_list",
        }
        layout=[2, 2, 2, 2, 1, 1]

    await bot.send_photo(
        message.chat.id,
        edit_car.photo,
        caption=send_text,
        reply_markup=get_custom_callback_btns(btns=btns, layout=layout)
    )
    await bot.delete_message(message.chat.id, int(edit_mes_id))
    await state.set_state(Statess.Admin_kbd)
    





############################ Проверка с выбором ###########################

@admin_edit_cars.callback_query(F.data.startswith("edit_flag"))
@admin_edit_cars.callback_query(F.data.startswith("edit_weel_drive"))
@admin_edit_cars.callback_query(F.data.startswith("edit_body"))
@admin_edit_cars.callback_query(F.data.startswith("edit_photo"))
@admin_edit_cars.callback_query(F.data.startswith("edit_engine_type"))
async def edit_car_param(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Обработчик выбора параметра для изменения."""
    await callback.message.delete()
    data = await state.get_data()
    car_id = data.get("car_id")
    
    if callback.data == "edit_flag":
        await callback.message.answer(
            "Выберите Флаг:", 
            reply_markup=get_custom_callback_btns(btns={
                'Популярный 🔥': '_популярные',
                'В пути 🗺️': '_в пути',
                'В наличии 🏁': '_в наличии',
                '❌': '_нет',
                'Назад':f'back_to_car_{car_id}'
            }, layout=[2,2]))
        await state.update_data(field = "flag")
        
    elif callback.data == "edit_weel_drive":
        await callback.message.answer(
            "Выберите привод автомобиля:", 
            reply_markup=get_custom_callback_btns(btns={
                'Передний': '_передний',
                'Задний': '_задний',
                'Полный': '_полный',
                'Назад':f'back_to_car_{car_id}'
            }, layout=[2,1,1]))
        await state.update_data(field = "weel_drive")

    elif callback.data == "edit_body":
        await callback.message.answer(
            "Выберите привод автомобиля:", 
            reply_markup=get_custom_callback_btns(btns={
                'Седан': '_Седан',
                'Хэтчбек': '_Хэтчбек',
                'Лифтбек': '_Лифтбек',
                'Универсал': '_Универсал',
                'Купе': '_Купе',
                'Кабриолет': '_Кабриолет',
                'Минивэн': '_Минивэн',
                'Микровэн': '_Микровэн',
                'Кроссовер': '_Кроссовер',
                'Внедорожник': '_Внедорожник',
                'Пикап': '_Пикап',
                'Лимузин': '_Лимузин',
                'Назад':f'back_to_car_{car_id}'
            }, layout=[2,2,2,2,2,2,1]))
        await state.update_data(field = "body")

    elif callback.data == "edit_engine_type":
        await callback.message.answer(
            "Выберите привод автомобиля:", 
            reply_markup=get_custom_callback_btns(btns={
                'ДВС': '_ДВС',
                'Гибрид': '_гибрид',
                'Электрический': '_электрический',
                'Назад':f'back_to_car_{car_id}'
            }, layout=[2,1,1]))
        await state.update_data(field = "engine_type")

    elif callback.data == "edit_photo":
        edit_mes_photo = await callback.message.answer(
            "Отправьте новое фото",
            reply_markup=get_custom_callback_btns(btns={
                'Назад':f'back_to_car_{car_id}'
            }, layout=[1]))
        await state.set_state(Statess.Edit_car_photo)
        await state.update_data(edit_mes_photo_id = edit_mes_photo.message_id)





@admin_edit_cars.callback_query(F.data.startswith("_ДВС"))
@admin_edit_cars.callback_query(F.data.startswith("_гибрид"))
@admin_edit_cars.callback_query(F.data.startswith("_электрический"))
@admin_edit_cars.callback_query(F.data.startswith("_Седан"))
@admin_edit_cars.callback_query(F.data.startswith("_Хэтчбек"))
@admin_edit_cars.callback_query(F.data.startswith("_Лифтбек"))
@admin_edit_cars.callback_query(F.data.startswith("_Универсал"))
@admin_edit_cars.callback_query(F.data.startswith("_Купе"))
@admin_edit_cars.callback_query(F.data.startswith("_Кабриолет"))
@admin_edit_cars.callback_query(F.data.startswith("_Минивэн"))
@admin_edit_cars.callback_query(F.data.startswith("_Микровэн"))
@admin_edit_cars.callback_query(F.data.startswith("_Кроссовер"))
@admin_edit_cars.callback_query(F.data.startswith("_Внедорожник"))
@admin_edit_cars.callback_query(F.data.startswith("_Пикап"))
@admin_edit_cars.callback_query(F.data.startswith("_Лимузин"))
@admin_edit_cars.callback_query(F.data.startswith("_популярные"))
@admin_edit_cars.callback_query(F.data.startswith("_в пути"))
@admin_edit_cars.callback_query(F.data.startswith("_в наличии"))
@admin_edit_cars.callback_query(F.data.startswith("_нет"))
@admin_edit_cars.callback_query(F.data.startswith("_передний"))
@admin_edit_cars.callback_query(F.data.startswith("_задний"))
@admin_edit_cars.callback_query(F.data.startswith("_полный"))
async def save_flag(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()

    new_value = callback.data.replace("_", "")
    data = await state.get_data()
    car_id = data.get("car_id")
    field = data.get("field")

    
    await update_car_field(session, car_id, field, new_value)

    edit_car = await orm_get_car(session, car_id)
    if edit_car.electrocar == "yes":
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Запас хода: {int_format(edit_car.power_reserve)} км
✅ Батарея: {int_format(edit_car.power_bank)} кВтч
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
                "Цена": "edit_cost",
                "Флаг": "edit_flag",
                "Пробег": "edit_route",
                "Запас хода": "edit_power_reserve",
                "Батарея": "edit_power_bank",
                "Привод": "edit_weel_drive",
                "Кузов": "edit_body",
                "Фото": "edit_photo",
                "Назад": "back_to_car_list",
            }
        layout=[2, 2, 2, 2, 1]
    else:
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Тип топлива: {edit_car.engine_type} 
✅ Объём двигателя: {edit_car.engine_volume} л
✅ Мощность: {int_format(edit_car.power)} л.с.
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
            "Цена":"edit_cost",
            "Флаг":"edit_flag",
            "Пробег":"edit_route",
            "Тип топлива":"edit_engine_type",
            "Объём двигателя":"edit_engine_volume",
            "Мощность":"edit_power",
            "Привод":"edit_weel_drive",
            "Кузов":"edit_body",
            "Фото":"edit_photo",
            "Назад":"back_to_car_list",
        }
        layout=[2, 2, 2, 2, 1, 1]

    await bot.send_photo(
        callback.message.chat.id,
        edit_car.photo,
        caption=send_text,
        reply_markup=get_custom_callback_btns(btns=btns, layout=layout)
    )



@admin_edit_cars.message(Statess.Edit_car_photo, F.photo | F.document)
async def save_car_photo(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    """Сохраняет новое фото автомобиля (пришедшее как фото или документ)."""
    await message.delete()
    data = await state.get_data()
    car_id = data.get("car_id")
    edit_mes = int(data.get("edit_mes_photo_id"))
    field = "photo"
    new_value = None

    # Если фото отправлено как документ с изображением
    if message.document and message.document.mime_type.startswith("image/"):
        new_value = message.document.file_id
    # Если фото отправлено как фото (список PhotoSize, выбираем самое большое)
    elif message.photo:
        new_value = message.photo[-1].file_id
    else:
        await bot.edit_message_text(
            "❌ Отправьте изображение, либо как фото, либо как документ с изображением",
            message.chat.id,
            edit_mes,
            reply_markup=get_custom_callback_btns(btns={
                'Назад':f'back_to_car_{car_id}'
            }, layout=[1])
            )
        return

    await update_car_field(session, car_id, field, new_value)
    await state.set_state(Statess.Admin_kbd)
    edit_car = await orm_get_car(session, car_id)
    if edit_car.electrocar == "yes":
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Запас хода: {int_format(edit_car.power_reserve)} км
✅ Батарея: {int_format(edit_car.power_bank)} кВтч
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
                "Цена": "edit_cost",
                "Флаг": "edit_flag",
                "Пробег": "edit_route",
                "Запас хода": "edit_power_reserve",
                "Батарея": "edit_power_bank",
                "Привод": "edit_weel_drive",
                "Кузов": "edit_body",
                "Фото": "edit_photo",
                "Назад": "back_to_car_list",
            }
        layout=[2, 2, 2, 2, 1]
    else:
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Тип топлива: {edit_car.engine_type} 
✅ Объём двигателя: {edit_car.engine_volume} л
✅ Мощность: {int_format(edit_car.power)} л.с.
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
            "Цена":"edit_cost",
            "Флаг":"edit_flag",
            "Пробег":"edit_route",
            "Тип топлива":"edit_engine_type",
            "Объём двигателя":"edit_engine_volume",
            "Мощность":"edit_power",
            "Привод":"edit_weel_drive",
            "Кузов":"edit_body",
            "Фото":"edit_photo",
            "Назад":"back_to_car_list",
        }
        layout=[2, 2, 2, 2, 1, 1]

    await bot.delete_message(message.chat.id, edit_mes)

    await bot.send_photo(
        message.chat.id,
        edit_car.photo,
        caption=send_text,
        reply_markup=get_custom_callback_btns(btns=btns, layout=layout)
    )





############################# Кнопки назад ############################


@admin_edit_cars.callback_query(F.data.startswith("back_to_car_list"))
async def edit_car_param(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()

    cars = await orm_get_cars(session)
    if not cars:
        await callback.message.answer("❌ В базе нет авто для редактирования")
        return
    if cars:
        btns = {f"{car_mark} {car_model} {int(car_cost)}": f"update_car_{car_id}" for car_id, car_mark, car_model, car_cost in cars}
        btns["Назад"] = "bback_"

    edit_mes = await callback.message.answer(
        "Выберите автомобиль для редактирования:",
reply_markup=get_callback_btns_single_row(btns=btns),
parse_mode='HTML'
    )
    await state.update_data(edit_mes_id = edit_mes.message_id)




@admin_edit_cars.callback_query(F.data.startswith("back_to_car_"))
async def back_to_edit_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Возвращает пользователя в меню редактирования автомобиля."""
    car_id_str = callback.data.replace("back_to_car_", "")
    car_id = int(car_id_str)
    
    await callback.message.delete()
    edit_car = await orm_get_car(session, car_id)
    if edit_car.electrocar == "yes":
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: {int_format(edit_car.cost)} $
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Запас хода: {int_format(edit_car.power_reserve)} км
✅ Батарея: {int_format(edit_car.power_bank)} кВтч
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
                "Цена": "edit_cost",
                "Флаг": "edit_flag",
                "Пробег": "edit_route",
                "Запас хода": "edit_power_reserve",
                "Батарея": "edit_power_bank",
                "Привод": "edit_weel_drive",
                "Кузов": "edit_body",
                "Фото": "edit_photo",
                "Назад": "back_to_car_list",
            }
        layout=[2, 2, 2, 2, 1]
    else:
        send_text = f'''
{edit_car.mark} {edit_car.model} {edit_car.package}, {edit_car.year} год

💰 Цена: ${int_format(edit_car.cost)}
🚩 Флаг: {edit_car.flag}

✅ Пробег: {int_format(edit_car.route)} км
✅ Тип топлива: {edit_car.engine_type} 
✅ Объём двигателя: {edit_car.engine_volume} л
✅ Мощность: {int_format(edit_car.power)} л.с.
✅ Привод: {edit_car.weel_drive}
✅ Кузов: {edit_car.body}
'''
        btns={
            "Цена":"edit_cost",
            "Флаг":"edit_flag",
            "Пробег":"edit_route",
            "Тип топлива":"edit_engine_type",
            "Объём двигателя":"edit_engine_volume",
            "Мощность":"edit_power",
            "Привод":"edit_weel_drive",
            "Кузов":"edit_body",
            "Фото":"edit_photo",
            "Назад":"back_to_car_list",
        }
        layout=[2, 2, 2, 2, 1, 1]

    del_mes = await bot.send_photo(
        callback.message.chat.id,
        edit_car.photo,
        caption=send_text,
        reply_markup=get_custom_callback_btns(btns=btns, layout=layout)
    )




@admin_edit_cars.callback_query(F.data.startswith("bback_"))
async def edit_car_param(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()

    await state.set_state(Statess.Admin_kbd)



