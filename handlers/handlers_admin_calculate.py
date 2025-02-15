import asyncio
import os
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Bot, types, F, Router
from aiogram.filters import Command, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from database.models import Cars
from database.orm_query import orm_add_DefQuestion, orm_add_admin, orm_add_car, orm_add_manager, orm_delete_DefQuestion, orm_delete_admin, orm_delete_car, orm_delete_manager, orm_get_DefQuestions, orm_get_admin, orm_get_admins, orm_get_calculate_column_value, orm_get_cars, orm_get_managers, orm_update_calculate_column
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

admin_calculate_router = Router()
admin_calculate_router.message.filter(ChatTypeFilter(['private'])) # Обрабатывает только личные сообщения с ботом
# user_group_router.message.middleware(AlbumMiddleware())


@admin_calculate_router.message(Statess.Admin_kbd, F.text.casefold().contains("расчёт стоимости"))  # Обработка кнопки "Управление доступом"
async def cancel_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    await message.delete()
    
    change_mes = await message.answer(f'''
<b>Изменение параметров расчёта:</b>

Минимальная сумма: <b>{await orm_get_calculate_column_value(session, "min_cost")} $</b> \n/change_min_sum  

Таможенный сбор: <b>{await orm_get_calculate_column_value(session, "custom")} $</b> \n/change_custom_sum

Комиссия РБ: <b>{await orm_get_calculate_column_value(session, "comis_rb")}%</b> \n/change_comis_rb

Банковская комиссия: <b>{await orm_get_calculate_column_value(session, "bank_comis")}%</b> \n/change_comis_bank

Доставка: <b>{await orm_get_calculate_column_value(session, "delivery")} $</b> \n/change_delivery_sum

Таможня ДВС Б/У 1500: <b>{await orm_get_calculate_column_value(session, "engine_volume_1500")} $</b> \n/change_dvs_1500

Таможня ДВС Б/У 1500-1800: <b>{await orm_get_calculate_column_value(session, "engine_volume_1500_1800")} $</b> \n/change_dvs_1500_1800

Таможня ДВС Б/У 1800-2300: <b>{await orm_get_calculate_column_value(session, "engine_volume_1800_2300")} $</b> \n/change_dvs_1800_2300
''', 
    parse_mode='HTML',
    reply_markup=get_custom_callback_btns(btns={'Назад':'main_menu_'}, layout=[1]))

    await state.update_data(change_mes_id = change_mes.message_id)

########################## Команды для изменения параметров расчёта ###########################

@admin_calculate_router.message(Statess.Admin_kbd, Command("change_min_sum"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новую минимальную сумму:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "min_cost")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_custom_sum"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новый таможенный сбор:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "custom")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_comis_rb"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новый процент комиссии РБ:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "comis_rb")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_comis_bank"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новый процент комисии банка:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "bank_comis")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_delivery_sum"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новую сумму доставки:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "delivery")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_dvs_1500"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новую комиссию для ДВС БУ и объёмом двигателя до 1500:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "engine_volume_1500")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_dvs_1500_1800"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новую комиссию для ДВС БУ и объёмом двигателя от 1500 до 1800:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "engine_volume_1500_1800")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Admin_kbd, Command("change_dvs_1800_2300"))
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")

    await bot.edit_message_text(
        "Введите новую комиссию для ДВС БУ и объёмом двигателя от 1800 до 2300:",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1])
    )
    await state.update_data(edit_column = "engine_volume_1800_2300")
    await state.set_state(Statess.Write_sum)


@admin_calculate_router.message(Statess.Write_sum, F.text)
async def send_welcome(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.delete()
    vokeb = await state.get_data()
    change_mes_id = vokeb.get("change_mes_id")
    edit_column = vokeb.get("edit_column")
    try:
        edit_value = float(message.text.replace(",", "."))
        if edit_column == "min_cost" and edit_value <= 0:
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nМинимальная сумма должна быть больше 0",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "custom" and edit_value <= 0:
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nМинимальная сумма должна быть больше 0",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "comis_rb" and (edit_value < 0 or edit_value > 100):
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nВводите значения от 0 до 100",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "bank_comis" and (edit_value < 0 or edit_value > 100):
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nВводите значения от 0 до 100",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "delivery" and edit_value <= 0:
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nВводите значения больше 0",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "engine_volume_1500" and edit_value <= 0:
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nВводите значения больше 0",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "engine_volume_1500_1800" and edit_value <= 0:
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nВводите значения больше 0",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
        elif edit_column == "engine_volume_1800_2300" and edit_value <= 0:
            await bot.edit_message_text(
            "❌ <b>Некорректное значение</b>\n\nВводите значения больше 0",
            message.chat.id,
            change_mes_id,
            reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
            parse_mode='HTML'
        )
            return
        
    except ValueError:
        await bot.edit_message_text(
        "❌ <b>Некорректное значение</b>\n\nВводите числовые значения, например 123 или 345,5",
        message.chat.id,
        change_mes_id,
        reply_markup=get_custom_callback_btns(btns={'Назад':'main_calculate_menu_'}, layout=[1]),
        parse_mode='HTML'
    )
        return

    await orm_update_calculate_column(session, edit_column, edit_value)

    await bot.edit_message_text(f'''
<b>Изменение параметров расчёта:</b>

Минимальная сумма: <b>{await orm_get_calculate_column_value(session, "min_cost")} $</b> \n/change_min_sum  

Таможенный сбор: <b>{await orm_get_calculate_column_value(session, "custom")} $</b> \n/change_custom_sum

Комиссия РБ: <b>{await orm_get_calculate_column_value(session, "comis_rb")}%</b> \n/change_comis_rb

Банковская комиссия: <b>{await orm_get_calculate_column_value(session, "bank_comis")}%</b> \n/change_comis_bank

Доставка: <b>{await orm_get_calculate_column_value(session, "delivery")} $</b> \n/change_delivery_sum

Таможня ДВС Б/У 1500: <b>{await orm_get_calculate_column_value(session, "engine_volume_1500")} $</b> \n/change_dvs_1500

Таможня ДВС Б/У 1500-1800: <b>{await orm_get_calculate_column_value(session, "engine_volume_1500_1800")} $</b> \n/change_dvs_1500_1800

Таможня ДВС Б/У 1800-2300: <b>{await orm_get_calculate_column_value(session, "engine_volume_1800_2300")} $</b> \n/change_dvs_1800_2300
''', 
    chat_id=message.chat.id,
    message_id=change_mes_id,
    parse_mode='HTML',
    reply_markup=get_custom_callback_btns(btns={'Назад':'main_menu_'}, layout=[1]))
    await state.set_state(Statess.Admin_kbd)




############################ Кнопки "Назад"  ###############################

@admin_calculate_router.callback_query(F.data.startswith("main_menu_"))
async def back_to_main(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await state.set_state(Statess.Admin_kbd)

@admin_calculate_router.callback_query(F.data.startswith("main_calculate_menu_"))
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    vokeb = await state.get_data()   
    change_mes_id = vokeb.get("change_mes_id", 0)
    await bot.edit_message_text(f'''
<b>Изменение параметров расчёта:</b>

Минимальная сумма: <b>{await orm_get_calculate_column_value(session, "min_cost")} $</b> \n/change_min_sum  

Таможенный сбор: <b>{await orm_get_calculate_column_value(session, "custom")} $</b> \n/change_custom_sum

Комиссия РБ: <b>{await orm_get_calculate_column_value(session, "comis_rb")}%</b> \n/change_comis_rb

Банковская комиссия: <b>{await orm_get_calculate_column_value(session, "bank_comis")}%</b> \n/change_comis_bank

Доставка: <b>{await orm_get_calculate_column_value(session, "delivery")} $</b> \n/change_delivery_sum

Таможня ДВС Б/У 1500: <b>{await orm_get_calculate_column_value(session, "engine_volume_1500")} $</b> \n/change_dvs_1500

Таможня ДВС Б/У 1500-1800: <b>{await orm_get_calculate_column_value(session, "engine_volume_1500_1800")} $</b> \n/change_dvs_1500_1800

Таможня ДВС Б/У 1800-2300: <b>{await orm_get_calculate_column_value(session, "engine_volume_1800_2300")} $</b> \n/change_dvs_1800_2300
''', 
    chat_id=callback.message.chat.id,
    message_id=change_mes_id,
    parse_mode='HTML',
    reply_markup=get_custom_callback_btns(btns={'Назад':'main_menu_'}, layout=[1]))
    await state.set_state(Statess.Admin_kbd)