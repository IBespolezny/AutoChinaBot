import asyncio
import os
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_car, orm_get_cars, orm_get_managers, orm_update_calculate_column
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

admin_auto_base_router = Router()
admin_auto_base_router.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())



############################################ кнопка "База автомобилей" ############################################

@admin_auto_base_router.message(Statess.Admin_kbd, F.text.casefold().contains("база автомобилей"))  # Обработка кнопки "Управление доступом"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Настройка фильтров", reply_markup=auto_settings.as_markup(
                            resize_keyboard=True))

    


########################### удалить автомобиль из базы ###########################

@admin_auto_base_router.message(Statess.Admin_kbd, F.text.casefold().contains("удалить автомобиль"))
async def show_car_list(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    await message.delete()
    
    # Получаем список автомобилей из базы
    cars = await orm_get_cars(session)

    if not cars:
        await message.answer("🚗 В базе нет автомобилей для удаления.")
        return

    # Формируем кнопки (по одной кнопке в строке)
    btns = {f"{car_mark} {car_model} {int(car_cost)}": f"delete_car_{car_id}" for car_id, car_mark, car_model, car_cost in cars}
    btns["Назад"] = "delCars_"
    keyboard = get_custom_callback_btns(btns=btns, layout=[1] * len(btns))  # Каждая строка содержит 1 кнопку

    delete_mes = await message.answer("Выберите автомобиль для удаления:", reply_markup=keyboard)
    await state.update_data(delete_mes=delete_mes.message_id)
    await state.set_state(Statess.delete_auto)



@admin_auto_base_router.callback_query(F.data.startswith("delete_car_"))
async def delete_selected_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    car_id = int(callback.data.split("_")[2])  # Получаем ID автомобиля из callback_data

    # Удаляем автомобиль
    delete_success = await orm_delete_car(session, car_id)

    # Убираем сообщение с кнопками
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"🚗 Автомобиль #️⃣{car_id} успешно удалён" if delete_success else "❌ Ошибка при удалении автомобиля."
    )

    await state.set_state(Statess.Admin_kbd)

@admin_auto_base_router.callback_query(F.data.startswith("delCars_"))
async def delete_selected_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()
    await state.set_state(Statess.Admin_kbd)






########################## Добавить автомобиль ############################


@admin_auto_base_router.message(Statess.Admin_kbd, F.text.casefold().contains("добавить автомобиль"))  # Обработка кнопки "Добавить автомобиль"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    # Получение сохраненного сообщения
    await message.delete()

    usemes = await message.answer(
        "Введите марку:",
        reply_markup=get_callback_btns(btns={
            '🔙 Назад': f'back_to_main_new',
        }),
        )
    mes = usemes.message_id
    await state.update_data(mes = mes)

    # Устанавливаем следующее состояние
    await state.set_state(Statess.Model)


@admin_auto_base_router.message(Statess.Model, F.text)  # Обработка кнопки "Автомобили по стоимости"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(mark = message.text)
    await message.delete()
    vokeb = await state.get_data()
    mes = int(vokeb.get("mes"))

    await bot.edit_message_text(
        "Введите модель:", 
        message.chat.id, 
        mes, 
        reply_markup=get_callback_btns(btns={
                '🔙 Назад': f'back_to_mark_{mes}',
            }),)
    await state.set_state(Statess.package)


@admin_auto_base_router.message(Statess.package, F.text)  # Обработка кнопки "Автомобили по стоимости"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(model = message.text)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите комплектацию:", 
        message.chat.id, 
        mes, 
        reply_markup=get_callback_btns(btns={
                '🔙 Назад': f'back_to_model_',
            }),)
    await state.set_state(Statess.body)


@admin_auto_base_router.message(Statess.body, F.text)  # Обработка кнопки "Автомобили по стоимости"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(package = message.text)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите кузов автомобиля:", 
        message.chat.id, 
        mes, 
        reply_markup=get_callback_btns(btns={
                '🔙 Назад': f'back_to_package_',
            }),)
    await state.set_state(Statess.Year)


@admin_auto_base_router.message(Statess.Year, F.text)  # Обработка кнопки "Автомобили по стоимости"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(body = message.text)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите год выпуска:", 
        message.chat.id, 
        mes, 
        reply_markup=get_callback_btns(btns={
                '🔙 Назад': f'back_to_body_{mes}',
            }),)
    await state.set_state(Statess.cost)


@admin_auto_base_router.message(Statess.cost, F.text)  # Обработка кнопки "Автомобили по стоимости"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    year = int(message.text)
    await state.update_data(year = year)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Укажите цену:", 
        message.chat.id, 
        mes, 
        reply_markup=get_callback_btns(btns={
                '🔙 Назад': f'back_to_year_{mes}',
            }),)
    await state.set_state(Statess.rools)




@admin_auto_base_router.message(Statess.rools, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    cost = float(message.text)
    await state.update_data(cost = cost)
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Укажите привод:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                'Передний': f'передний',
                'Задний': f'задний',
                'Полный': f'полный',
                '🔙 Назад': f'back_to_cost_',
            }, layout=[3,1]
            ),)
    await state.set_state(None)


@admin_auto_base_router.callback_query(F.data.startswith("передний"))
@admin_auto_base_router.callback_query(F.data.startswith("задний"))
@admin_auto_base_router.callback_query(F.data.startswith("полный"))
async def choos_engine_type(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):

    await state.update_data(weel_drive = callback.data)
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Как отметить автомобиль:", 
        callback.message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                'Популярный 🔥': 'популярные',
                'В пути 🗺️': 'в пути',
                'В наличии 🏁': 'в наличии',
                '❌': 'нет',
                '🔙 Назад': 'back_to_weel_drive',
            }, layout=[2,2,1]
            ),)





@admin_auto_base_router.callback_query(F.data.startswith("популярные"))
@admin_auto_base_router.callback_query(F.data.startswith("в пути"))
@admin_auto_base_router.callback_query(F.data.startswith("в наличии"))
@admin_auto_base_router.callback_query(F.data.startswith("нет"))
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    
    await state.update_data(flag = callback.data)
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Укажите тип двигателя:", 
        callback.message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                'ДВС': f'ДВС',
                'Электро': f'электрический',
                'Гибрид': f'гибрид',
                '🔙 Назад': f'back_to_flag',
            }, layout=[3,1]
            ),)


@admin_auto_base_router.callback_query(F.data.startswith("ДВС"))
@admin_auto_base_router.callback_query(F.data.startswith("электрический"))
@admin_auto_base_router.callback_query(F.data.startswith("гибрид"))
async def choos_engine_type(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    vokeb = await state.get_data()
    mes = vokeb.get("mes")
    await state.update_data(engine_type = callback.data)

    if callback.data == "электрический":
        await bot.edit_message_text(
        "Введите мощность электроавтомобиля:", 
        callback.message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_engine_type',
            }, layout=[1]
            ),)
        
        await state.update_data(electrocar="yes")
        await state.set_state(Statess.power)
        

    if callback.data != "электрический":
        await bot.edit_message_text(
        "Введите объём двигателя:", 
        callback.message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_engine_type',
            }, layout=[1]
            ),)
        
        await state.update_data(electrocar="no")
        await state.set_state(Statess.engine_volume)


@admin_auto_base_router.message(Statess.power, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    power = float(message.text)
    await state.update_data(power = power)
    await state.update_data(engine_volume = None)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите ёмкость батареи:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_power',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.power_bank)    


@admin_auto_base_router.message(Statess.power_bank, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    power_bank = float(message.text)
    await state.update_data(power_bank = power_bank)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите запас хода:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_bank_power',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.power_reserve)  


@admin_auto_base_router.message(Statess.power_reserve, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    power_reserve = float(message.text)
    await state.update_data(power_reserve = power_reserve)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите пробег:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_reserv_power',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.route)  


@admin_auto_base_router.message(Statess.engine_volume, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    engine_volume = float(message.text)
    await state.update_data(engine_volume = engine_volume)
    await state.update_data(power_bank = None)
    await state.update_data(power_reserve = None)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите мощность в Лошадинных силах:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_type_of_engine',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.power_engin) 

@admin_auto_base_router.message(Statess.power_engin, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    power = float(message.text)
    await state.update_data(power = power)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Введите пробег:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_engine_volume',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.route) 


@admin_auto_base_router.message(Statess.route, F.text)
async def choos_engine_type(message: types.Message, state: FSMContext, session: AsyncSession):
    route = float(message.text)
    await state.update_data(route = route)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    await bot.edit_message_text(
        "Отправьте фото автомобиля:", 
        message.chat.id, 
        mes, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_route',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.photo) 



@admin_auto_base_router.message(Statess.photo, F.photo)  # Обработка кнопки "Автомобили по стоимости"
async def cancel_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    photo = message.photo[-1].file_id
    await state.update_data(photo = photo)
    await message.delete()
    vokeb = await state.get_data()
    mes = vokeb.get("mes")

    vokeb = await state.get_data()
    await orm_add_car(session, vokeb)
    await bot.edit_message_text(
        f"Данные записаны!", 
        message.chat.id, 
        mes, 
        reply_markup=get_callback_btns(btns={
                'ОК ✅': f'back_to_main_new_{mes}',
            }),)









########################## Кнопки назад ###########################

# Обработчики кнопок "Назад"

@admin_auto_base_router.callback_query(F.data.startswith("back_to_main_new"))
async def back_to_main(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.delete_message(
        callback.message.chat.id,
        mesID,
    )
    await state.set_state(Statess.Admin_kbd)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_mark_"))
async def back_to_mark(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите марку:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_main_new'})
    )
    await state.set_state(Statess.Model)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_model_"))
async def back_to_model(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите модель:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_mark_'})
    )
    await state.set_state(Statess.package)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_package_"))
async def back_to_package(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите комплектацию:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_model_'})
    )
    await state.set_state(Statess.body)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_body_"))
async def back_to_body(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите кузов автомобиля:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_package_'})
    )
    await state.set_state(Statess.Year)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_year_"))
async def back_to_year(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите год выпуска:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_body_'})
    )
    await state.set_state(Statess.cost)


@admin_auto_base_router.callback_query(F.data.startswith("back_to_type_of_engine"))
async def back_to_year(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите объём двигателя:", 
        callback.message.chat.id, 
        mesID, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_engine_type',
            }, layout=[1]
            ),)
    await state.set_state(Statess.engine_volume)


@admin_auto_base_router.callback_query(F.data.startswith("back_to_cost_"))
async def back_to_cost(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Укажите цену:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_year_'})
    )
    await state.set_state(Statess.rools)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_engine_type"))
async def back_to_engine_type(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Укажите тип двигателя:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={
            'ДВС': 'ДВС',
            'Электро': 'электрический',
            'Гибрид': 'гибрид',
            '🔙 Назад': 'back_to_cost_'
        }, layout=[3,1])
    )


@admin_auto_base_router.callback_query(F.data.startswith("back_to_route"))
async def back_to_route(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите пробег:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={'🔙 Назад': 'back_to_power_bank'}, layout=[1])
    )
    await state.set_state(Statess.route)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_bank_power"))
async def back_to_power_bank(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите ёмкость батареи:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={'🔙 Назад': 'back_to_power'}, layout=[1])
    )
    await state.set_state(Statess.power_bank)

@admin_auto_base_router.callback_query(F.data.startswith("back_to_power"))
async def back_to_power(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите мощность электроавтомобиля:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={'🔙 Назад': 'back_to_engine_type'}, layout=[1])
    )
    await state.set_state(Statess.power)


@admin_auto_base_router.callback_query(F.data.startswith("back_to_reserv_power"))
async def back_to_power(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите запас хода:", 
        callback.message.chat.id, 
        mesID, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_bank_power',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.power_reserve) 




@admin_auto_base_router.callback_query(F.data.startswith("back_to_weel_drive"))
async def back_to_power(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Укажите привод:", 
        callback.message.chat.id, 
        mesID, 
        reply_markup=get_custom_callback_btns(btns={
                'Передний': f'передний',
                'Задний': f'задний',
                'Полный': f'полный',
                '🔙 Назад': f'back_to_engine_type',
            }, layout=[3,1]
            ),)
    await state.set_state(None)


@admin_auto_base_router.callback_query(F.data.startswith("back_to_flag"))
async def back_to_power(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Как отметить автомобиль:", 
        callback.message.chat.id, 
        mesID, 
        reply_markup=get_custom_callback_btns(btns={
                'Популярный 🔥': 'популярные',
                'В пути 🗺️': 'в пути',
                'В наличии 🏁': 'в наличии',
                '❌': 'нет',
                '🔙 Назад': 'back_to_weel_drive',
            }, layout=[2,2,1]
            ),)


@admin_auto_base_router.callback_query(F.data.startswith("back_to_engine_volume"))
async def back_to_power(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id

    await bot.edit_message_text(
        "Введите мощность в Лошадинных силах:", 
        callback.message.chat.id, 
        mesID, 
        reply_markup=get_custom_callback_btns(btns={
                '🔙 Назад': 'back_to_type_of_engine',
            }, layout=[1]
            ),)
        
    await state.set_state(Statess.power_engin) 
