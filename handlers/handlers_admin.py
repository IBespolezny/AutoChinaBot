import asyncio
import os
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_cars, orm_get_managers
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

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())

#################################   Команды Администратора   #################################

@admin_router.message(StateFilter('*'), Command("admin"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)

    if message.from_user.id in admins_ids:
        name = adminss.get(message.from_user.id)    # Получение имени админа по ID
        await message.answer(f"Добро пожаловать, {name}", reply_markup=admin_menu.as_markup(
                            resize_keyboard=True))
        await state.set_state(Statess.Admin_kbd)





############################################ кнопка "Управление доступом" ############################################

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("управление доступом"))  # Обработка кнопки "Управление доступом"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer("Настройка доступа", reply_markup=access_settings.as_markup(
                            resize_keyboard=True))


##### Администраторы

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("администраторы"))  # Обработка кнопки "администраторы"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer("Управление Администраторами", reply_markup=admin_settings.as_markup(
                            resize_keyboard=True))
    await state.set_state(Statess.Admin_settings)
    

@admin_router.message(Statess.Admin_settings, F.text.casefold().contains("добавить"))  # Обработка кнопки "добавить"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.delete()
    admins_ids, adminss, managers_ids, managerss = await get_admins_and_managers(session)

    if message.from_user.id in admins_ids:
        delmes = await message.answer("Как зовут Администратора?", reply_markup=get_custom_callback_btns(
            btns={"Назад":"admin_"}, layout=[1]))
        await state.set_state(Statess.add_admin_name)
        

@admin_router.message(Statess.add_admin_name, F.text)  # Добавляет id админа
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(name = message.text)
    await message.delete()

    delmes = await message.answer("Отправьте id Администратора:", reply_markup=get_custom_callback_btns(
            btns={"Назад":"admin_"}, layout=[1]))
    await state.set_state(Statess.add_admin_id)


@admin_router.message(Statess.add_admin_id, F.text)  # Добавляет админа в БД
async def cancel_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    adminId = int(message.text)
    await state.update_data(id = adminId)
    await message.delete()
    vokeb = await state.get_data()

    await orm_add_admin(session, vokeb)
    await state.set_state(Statess.Admin_settings)
    await message.answer("Добавлен новый Администратор!", reply_markup=admin_settings.as_markup(
                            resize_keyboard=True))
    

@admin_router.message(Statess.Admin_settings, F.text.casefold().contains("удалить"))  # Обработка кнопки "удалить"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    admins = await orm_get_admins(session) # Получение админов из БД

    adminss = {admin.name: f"{admin.id}" for admin in admins}

    admins = [int(admin) for admin in adminss.values()]
    
    if message.from_user.id in admins:
        await message.delete()
        admins = await orm_get_admins(session)

        adminess = {admin.name: f"delAdmin_{admin.id}" for admin in admins}
        adminess["Назад"] = "admin_"

        await message.answer("Выберите администратора для удаления:", reply_markup=get_callback_btns(btns=adminess))


@admin_router.callback_query(F.data.startswith("delAdmin_")) # Обаботчик для удаления Администратора по id
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession):
    # Удаляем сообщение с клавиатурой
    await callback.message.delete()
    admin = callback.data.replace("delAdmin_", "")

    await orm_delete_admin(session, int(admin))
    delmes = await callback.message.answer("Администратор удалён!")
    await asyncio.sleep(5)
    await bot.delete_message(callback.message.chat.id, delmes.message_id)



@admin_router.message(Statess.Admin_settings, F.text.casefold().contains("список администраторов"))  # Обработка кнопки "удалить"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    admins = await orm_get_admins(session) # Получение админов из БД
    managers = await orm_get_managers(session) # Получение менеджеров из БД

    adminss = {admin.name: f"{admin.id}" for admin in admins}
    managerss = {manager.name : f"{manager.id}" for manager in managers}

    admins = [int(admin) for admin in adminss.values()]
    managers = [int(manager) for manager in managerss.values()]
    await message.delete()
    
    if message.from_user.id in admins:
        admins = await orm_get_admins(session)

        adminess = {admin.name: f"admin_{admin.id}" for admin in admins}
        adminess["Назад"] = "admin_"

        await message.answer("Список Администраторов:", reply_markup=get_callback_btns(btns=adminess))

@admin_router.message(Statess.Admin_settings, F.text.casefold().contains("назад"))  # Обработка кнопки "менеджеры"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.delete()
    await state.set_state(Statess.Admin_kbd)
    await message.answer("Назад🔙", reply_markup=access_settings.as_markup(
                            resize_keyboard=True))

##### Менеджеры

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("менеджеры"))  # Обработка кнопки "менеджеры"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer("Управление Менеджерами", reply_markup=manager_settings.as_markup(
                            resize_keyboard=True))
    await state.set_state(Statess.Manager_settings)


@admin_router.message(Statess.Manager_settings, F.text.casefold().contains("список менеджеров"))  # Обработка кнопки "список менеджеров"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.delete()
    admins = await orm_get_admins(session) # Получение админов из БД
    managers = await orm_get_managers(session) # Получение менеджеров из БД

    adminss = {admin.name: f"{admin.id}" for admin in admins}
    managerss = {manager.name : f"{manager.id}" for manager in managers}

    admins = [int(admin) for admin in adminss.values()]
    managers = [int(manager) for manager in managerss.values()]

    if (message.from_user.id in admins ) | (message.from_user.id in managers):
        managers = await orm_get_managers(session)

        managerss = {manager.name: f"manager_{manager.id}" for manager in managers}
        managerss["Назад"] = "manager_"

        await message.answer("Список Менеджеров:", reply_markup=get_callback_btns(btns=managerss))


@admin_router.message(Statess.Manager_settings, F.text.casefold().contains("добавить"))  # Обработка кнопки "добавить"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.delete()
    admins = await orm_get_admins(session) # Получение админов из БД

    adminss = {admin.name: f"{admin.id}" for admin in admins}

    admins = [int(admin) for admin in adminss.values()]

    if message.from_user.id in admins:
        delmes = await message.answer("Как зовут Менеджера?", reply_markup=get_custom_callback_btns(
            btns={"Назад":"manager_"}, layout=[1]))
        await state.set_state(Statess.add_manager_name)


@admin_router.message(Statess.add_manager_name, F.text)  # Добавляет id менеджера
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.update_data(name = message.text)
    await message.delete()

    await message.answer("Отправьте id Менеджера:", reply_markup=get_custom_callback_btns(
            btns={"Назад":"manager_"}, layout=[1]))
    await state.set_state(Statess.add_manager_id)


@admin_router.message(Statess.add_manager_id, F.text)  # Добавляет менеджера в БД
async def cancel_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(id = int(message.text))
    await message.delete()
    vokeb = await state.get_data()

    await orm_add_manager(session, vokeb)
    await state.set_state(Statess.Manager_settings)
    await message.answer("Добавлен новый менеджер!", reply_markup=manager_settings.as_markup(
                            resize_keyboard=True))


@admin_router.message(Statess.Manager_settings, F.text.casefold().contains("удалить"))  # Обработка кнопки "добавить"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.delete()
    admins = await orm_get_admins(session) # Получение админов из БД

    adminss = {admin.name: f"{admin.id}" for admin in admins}

    admins = [int(admin) for admin in adminss.values()]

    if message.from_user.id in admins:
        managers = await orm_get_managers(session)

        managerss = {manager.name: f"delManager_{manager.id}" for manager in managers}
        managerss["Назад"] = "manager_"

        await message.answer("Выберите менеджера для удаления:", reply_markup=get_callback_btns(btns=managerss))


@admin_router.callback_query(F.data.startswith("delManager_")) # Обаботчик для удаления Менеджера по id
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession):
    # Удаляем сообщение с клавиатурой
    await callback.message.delete()
    manager = callback.data.replace("delManager_", "")

    await orm_delete_manager(session, int(manager))
    delmes = await callback.message.answer("Менеджер удалён!")



@admin_router.message(Statess.Manager_settings, F.text.casefold().contains("назад"))  # Обработка кнопки "назад"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.delete()
    await state.set_state(Statess.Admin_kbd)
    await message.answer("Назад🔙", reply_markup=access_settings.as_markup(
                            resize_keyboard=True))


##### Назад и прочее

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("назад"))  # Обработка кнопки "назад"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    await message.answer("Главное меню🔙", reply_markup=admin_menu.as_markup(
                            resize_keyboard=True))

@admin_router.callback_query(F.data.startswith("manager_")) # Обаботчик для удаления списка Менеджеров
async def inline_button_handler(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем сообщение с клавиатурой
    await callback.message.delete()
    await state.set_state(Statess.Manager_settings)


@admin_router.callback_query(F.data.startswith("admin_")) # Обаботчик для удаления списка Администраторов
async def inline_button_handler(callback_query: types.CallbackQuery, state: FSMContext):
    # Удаляем сообщение с клавиатурой
    await callback_query.message.delete()
    await state.set_state(Statess.Admin_settings)















############################################ кнопка "База автомобилей" ############################################

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("база автомобилей"))  # Обработка кнопки "Управление доступом"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Настройка фильтров", reply_markup=auto_settings.as_markup(
                            resize_keyboard=True))

    




########################### удалить автомобиль из базы ###########################

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("удалить автомобиль"))
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



@admin_router.callback_query(F.data.startswith("delete_car_"))
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

@admin_router.callback_query(F.data.startswith("delCars_"))
async def delete_selected_car(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()
    await state.set_state(Statess.Admin_kbd)






########################## Добавить автомобиль ############################


@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("добавить автомобиль"))  # Обработка кнопки "Добавить автомобиль"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    # Получение сохраненного сообщения
    await message.delete()
    # delMEs = await message.answer("Загрузка базы данных...", reply_markup=ReplyKeyboardRemove())
    # await bot.delete_message(message.chat.id, delMEs.message_id)

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


@admin_router.message(Statess.Model, F.text)  # Обработка кнопки "Автомобили по стоимости"
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


@admin_router.message(Statess.package, F.text)  # Обработка кнопки "Автомобили по стоимости"
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


@admin_router.message(Statess.body, F.text)  # Обработка кнопки "Автомобили по стоимости"
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


@admin_router.message(Statess.Year, F.text)  # Обработка кнопки "Автомобили по стоимости"
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


@admin_router.message(Statess.cost, F.text)  # Обработка кнопки "Автомобили по стоимости"
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




@admin_router.message(Statess.rools, F.text)
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


@admin_router.callback_query(F.data.startswith("передний"))
@admin_router.callback_query(F.data.startswith("задний"))
@admin_router.callback_query(F.data.startswith("полный"))
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





@admin_router.callback_query(F.data.startswith("популярные"))
@admin_router.callback_query(F.data.startswith("в пути"))
@admin_router.callback_query(F.data.startswith("в наличии"))
@admin_router.callback_query(F.data.startswith("нет"))
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


@admin_router.callback_query(F.data.startswith("ДВС"))
@admin_router.callback_query(F.data.startswith("электрический"))
@admin_router.callback_query(F.data.startswith("гибрид"))
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


@admin_router.message(Statess.power, F.text)
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


@admin_router.message(Statess.power_bank, F.text)
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


@admin_router.message(Statess.power_reserve, F.text)
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


@admin_router.message(Statess.engine_volume, F.text)
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

@admin_router.message(Statess.power_engin, F.text)
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


@admin_router.message(Statess.route, F.text)
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



@admin_router.message(Statess.photo, F.photo)  # Обработка кнопки "Автомобили по стоимости"
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

@admin_router.callback_query(F.data.startswith("back_to_main_new"))
async def back_to_main(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.delete_message(
        callback.message.chat.id,
        mesID,
    )
    await state.set_state(Statess.Admin_kbd)

@admin_router.callback_query(F.data.startswith("back_to_mark_"))
async def back_to_mark(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите марку:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_main_new'})
    )
    await state.set_state(Statess.Model)

@admin_router.callback_query(F.data.startswith("back_to_model_"))
async def back_to_model(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите модель:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_mark_'})
    )
    await state.set_state(Statess.package)

@admin_router.callback_query(F.data.startswith("back_to_package_"))
async def back_to_package(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите комплектацию:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_model_'})
    )
    await state.set_state(Statess.body)

@admin_router.callback_query(F.data.startswith("back_to_body_"))
async def back_to_body(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите кузов автомобиля:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_package_'})
    )
    await state.set_state(Statess.Year)

@admin_router.callback_query(F.data.startswith("back_to_year_"))
async def back_to_year(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите год выпуска:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_body_'})
    )
    await state.set_state(Statess.cost)


@admin_router.callback_query(F.data.startswith("back_to_type_of_engine"))
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


@admin_router.callback_query(F.data.startswith("back_to_cost_"))
async def back_to_cost(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Укажите цену:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_callback_btns(btns={'🔙 Назад': 'back_to_year_'})
    )
    await state.set_state(Statess.rools)

@admin_router.callback_query(F.data.startswith("back_to_engine_type"))
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


@admin_router.callback_query(F.data.startswith("back_to_route"))
async def back_to_route(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите пробег:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={'🔙 Назад': 'back_to_power_bank'}, layout=[1])
    )
    await state.set_state(Statess.route)

@admin_router.callback_query(F.data.startswith("back_to_bank_power"))
async def back_to_power_bank(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите ёмкость батареи:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={'🔙 Назад': 'back_to_power'}, layout=[1])
    )
    await state.set_state(Statess.power_bank)

@admin_router.callback_query(F.data.startswith("back_to_power"))
async def back_to_power(callback: types.CallbackQuery, state: FSMContext) -> None:
    mesID = callback.message.message_id
    await bot.edit_message_text(
        "Введите мощность электроавтомобиля:",
        callback.message.chat.id,
        mesID,
        reply_markup=get_custom_callback_btns(btns={'🔙 Назад': 'back_to_engine_type'}, layout=[1])
    )
    await state.set_state(Statess.power)


@admin_router.callback_query(F.data.startswith("back_to_reserv_power"))
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




@admin_router.callback_query(F.data.startswith("back_to_weel_drive"))
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


@admin_router.callback_query(F.data.startswith("back_to_flag"))
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


@admin_router.callback_query(F.data.startswith("back_to_engine_volume"))
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






############################################ кнопка "Частые вопросы" ############################################

@admin_router.message(Statess.Admin_kbd, F.text.casefold().contains("частые вопросы"))  # Обработка кнопки "частые вопросы"
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.answer("Выберите действие:", reply_markup=add_del_back_menu.as_markup(
                            resize_keyboard=True))
    await state.set_state(Statess.DefQuestion_set)


@admin_router.message(Statess.DefQuestion_set, F.text.casefold().contains("добавить"))  # Добавление вопроса
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await message.answer("Введите новый вопрос:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.DefQuestion_add)


@admin_router.message(Statess.DefQuestion_add, F.text)  # Добавление вопроса
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    question = message.text
    await message.delete()

    await state.update_data(question = question)
    await message.answer("Введите ответ на вопрос:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Statess.add_DefAnswer)


@admin_router.message(Statess.add_DefAnswer, F.text)  # Добавление ответа
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    await state.update_data(answer = message.text)
    await message.delete()

    vokeb = await state.get_data()

    await orm_add_DefQuestion(session, vokeb)
    await state.set_state(Statess.DefQuestion_set)
    await message.answer("Добавлен новый вопрос!", reply_markup=add_del_back_menu.as_markup(
                            resize_keyboard=True))


@admin_router.message(Statess.DefQuestion_set, F.text.casefold().contains("удалить"))  # Удаление вопроса
async def cancel_handler(message: types.Message, state: FSMContext, session:AsyncSession) -> None:
    questions = await orm_get_DefQuestions(session) # Получение админов из БД

    questionss = {question.question: f"delQuestion_{question.id}" for question in questions}
    questionss["Назад"] = "questions_"

    await message.answer("Выберите вопрос для удаления:", reply_markup=get_callback_btns_single_row(btns=questionss, sizes=(1,)))


@admin_router.callback_query(F.data.startswith("delQuestion_")) # Обаботчик для удаления Вопроса по id
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession):
    # Удаляем сообщение с клавиатурой
    await callback.message.delete()
    question = callback.data.replace("delQuestion_", "")

    await orm_delete_DefQuestion(session, int(question))
    await callback.message.answer("Вопрос удалён!")


@admin_router.message(Statess.DefQuestion_set, F.text.casefold().contains("назад"))  # Обработка кнопки "Назад"
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Statess.Admin_kbd)
    await message.answer("Выберите вариант", reply_markup=admin_menu.as_markup(
                            resize_keyboard=True))
    
@admin_router.callback_query(F.data.startswith("questions_")) # Обаботчик для удаления Вопроса по id
async def inline_button_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Statess.DefQuestion_set)