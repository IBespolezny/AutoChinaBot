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
