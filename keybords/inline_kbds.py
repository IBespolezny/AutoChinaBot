from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

#Создать CallBack кнопки
def get_callback_btns(
    *, 
    btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        if isinstance(data, tuple) and data[0] == 'url':
            # Если значение кортежа, то это кнопка-ссылка
            keyboard.add(InlineKeyboardButton(text=text, url=data[1]))
        else:
            # Иначе, это кнопка для callback
            keyboard.add(InlineKeyboardButton(text=text, callback_data=str(data)))  # Убедитесь, что callback_data - строка

    return keyboard.adjust(*sizes).as_markup()


def get_callback_btns_single_row(
    *, 
    btns: dict[str, str], sizes: tuple[int] = (1,)):

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        if isinstance(data, tuple) and data[0] == 'url':
            # Если значение кортежа, то это кнопка-ссылка
            keyboard.add(InlineKeyboardButton(text=text, url=data[1]))
        else:
            # Иначе, это кнопка для callback
            keyboard.add(InlineKeyboardButton(text=text, callback_data=str(data)))  # Убедитесь, что callback_data - строка

    return keyboard.adjust(*sizes).as_markup()  # Добавляем adjust для расположения кнопок по одному в ряду
