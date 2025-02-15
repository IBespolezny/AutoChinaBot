import asyncio
import os
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_dialog, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_cars, orm_get_managers, orm_get_managers_group, orm_update_calculate_column
from filters.chat_filters import ChatTypeFilter
import config

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from functions.functions import get_admins_and_managers
from handlers.handlers_user import Statess
from keybords.inline_kbds import get_callback_btns, get_callback_btns_single_row, get_custom_callback_btns, orm_delete_car_buttons
from keybords.return_kbds import region_menu, engine_menu, old_or_new_menu, main_menu
# from keybords.inline_kbds import get_callback_btns

bot = Bot(token=os.getenv("API_TOKEN"))


#################################   Фильтр групп   #################################

user_select_car = Router()
user_select_car.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())



#######################################     Подобрать автомобиль    ###########################################

@user_select_car.message(F.text.casefold().contains("подобрать автомобиль"))   # Логика Подобрать автомобиль
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите регион:", reply_markup=region_menu.as_markup(
                            resize_keyboard=True))
    await state.set_state(Statess.help_buy_auto)
    


@user_select_car.message(Statess.help_buy_auto, F.text.casefold().contains("рф"))
@user_select_car.message(Statess.help_buy_auto, F.text.casefold().contains("рб"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    region = message.text
    await state.update_data(region = region)
    await message.answer("Выберите тип двигателя:", reply_markup=engine_menu.as_markup(
                            resize_keyboard=True))


@user_select_car.message(Statess.help_buy_auto, F.text.casefold().contains("двс"))
@user_select_car.message(Statess.help_buy_auto, F.text.casefold().contains("электрический"))   # Логика Расчитать стоимость автомобиля
async def hot_handler(message: types.Message, state: FSMContext) -> None:
    engine_type = message.text
    await state.update_data(engine_type = engine_type)
    await message.answer("Выберите тип автомобиля:", reply_markup=old_or_new_menu.as_markup(
                            resize_keyboard=True))


@user_select_car.message(Statess.help_buy_auto, F.text.casefold().contains("новый"))
@user_select_car.message(Statess.help_buy_auto, F.text.casefold().contains("б/у"))   # Логика Расчитать стоимость автомобиля
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

