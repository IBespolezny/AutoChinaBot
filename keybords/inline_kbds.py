from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Cars

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



def get_custom_callback_btns(
    *, 
    btns: dict[str, str], 
    layout: list[int]
):
    """
    Создаёт кастомную клавиатуру с кнопками.

    :param btns: Словарь кнопок {текст: callback_data или ('url', url)}.
    :param layout: Список, задающий количество кнопок в рядах, например [1, 2, 1].
    :return: InlineKeyboardMarkup.
    """
    keyboard = InlineKeyboardBuilder()

    # Сохраняем кнопки в очередь
    button_queue = []
    for text, data in btns.items():
        if isinstance(data, tuple) and data[0] == 'url':
            # Если значение кортежа, то это кнопка-ссылка
            button_queue.append(InlineKeyboardButton(text=text, url=data[1]))
        else:
            # Иначе, это кнопка для callback
            button_queue.append(InlineKeyboardButton(text=text, callback_data=str(data)))

    # Распределяем кнопки по рядам на основе layout
    index = 0
    for row_size in layout:
        if index >= len(button_queue):
            break
        row_buttons = button_queue[index:index + row_size]
        keyboard.row(*row_buttons)
        index += row_size

    # Возвращаем разметку
    return keyboard.as_markup()


CARS_PER_PAGE = 9  # Количество автомобилей на одной странице

async def orm_delete_car_buttons(session: AsyncSession, page: int = 0):
    """Создаёт клавиатуру с 9 автомобилями на странице и кнопками управления."""
    result = await session.execute(select(Cars))
    cars = result.scalars().all()
    
    total_pages = (len(cars) - 1) // CARS_PER_PAGE + 1  # Всего страниц
    start = page * CARS_PER_PAGE
    end = start + CARS_PER_PAGE
    paginated_cars = cars[start:end]

    keyboard = InlineKeyboardBuilder()

    # Добавляем кнопки автомобилей (по одной в строке)
    for car in paginated_cars:
        button_text = f"{car.mark} {car.model} {car.package}, {car.year}"
        keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"delete_car_{car.car_id}"))

    # Кнопки управления страницами (⬅️ и ➡️ в одной строке)
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"pagination_{page-1}"))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"pagination_{page+1}"))

    if navigation_buttons:
        keyboard.row(*navigation_buttons)  # Кнопки навигации в одной строке

    return keyboard.as_markup()