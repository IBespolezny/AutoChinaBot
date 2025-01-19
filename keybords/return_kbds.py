from aiogram.types import KeyboardButtonPollType, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Создаем клавиатуру с кнопкой запроса контакта
# number_kb = ReplyKeyboardMarkup(
#     keyboard=[
#         [KeyboardButton(text="Отправить номер📞", request_contact=True)]
#     ],
#     resize_keyboard=True,
#     one_time_keyboard=True
# )


main_menu = ReplyKeyboardBuilder()                              # Главная клавиатура
main_menu.add(
    KeyboardButton(text="Подобрать автомобиль🚘"),
    KeyboardButton(text="Расчитать стоимость автомобиля💰"),
    KeyboardButton(text="Горячие предложения🔥"),
    KeyboardButton(text="Вопросы и ответы❔"),

)
main_menu.adjust(2,2)


hot_menu = ReplyKeyboardBuilder()                               # Клавиатура кнопки "Горячие предложения"
hot_menu.add(
    KeyboardButton(text="Назад🔙"),
    KeyboardButton(text="Подборка автомобилей по стоимости"),
    KeyboardButton(text="Популярные автомобили🔥"),
    KeyboardButton(text="Электроавтомобили"),
    KeyboardButton(text="Автомобили в пути"),
    KeyboardButton(text="Автомобили в наличии"),
)
hot_menu.adjust(2,2,2)


question_menu = ReplyKeyboardBuilder()                          # Клавиатура кнопки "Вопросы и ответы"
question_menu.add(
    KeyboardButton(text="Назад🔙"),
    KeyboardButton(text="Частые вопросы❓"),
    KeyboardButton(text="Задать вопрос"),
)
question_menu.adjust(1,2)


admin_menu = ReplyKeyboardBuilder()                          # Клавиатура Администратора
admin_menu.add(
    KeyboardButton(text="Управление доступом"),
    KeyboardButton(text="База автомобилей"),
    KeyboardButton(text="Частые вопросы"),
)
admin_menu.adjust(1,2)


access_settings = ReplyKeyboardBuilder()                          # Клавиатура кнопки "Управление доступом"
access_settings.add(
    KeyboardButton(text="Администраторы"),
    KeyboardButton(text="Менеджеры"),
    KeyboardButton(text="Назад🔙"),
)
access_settings.adjust(2,1)


admin_settings = ReplyKeyboardBuilder()                          # Клавиатура кнопки "Администраторы"
admin_settings.add(
    KeyboardButton(text="Добавить"),
    KeyboardButton(text="Удалить"),
    KeyboardButton(text="Назад🔙"),
    KeyboardButton(text="Список Администраторов"),
)
admin_settings.adjust(2,2)


manager_settings = ReplyKeyboardBuilder()                          # Клавиатура кнопки "Менеджеры"
manager_settings.add(
    KeyboardButton(text="Добавить"),
    KeyboardButton(text="Удалить"),
    KeyboardButton(text="Назад🔙"),
    KeyboardButton(text="Список Менеджеров"),
)
manager_settings.adjust(2,2)


auto_settings = ReplyKeyboardBuilder()                          # Клавиатура кнопки "База автомобилей"
auto_settings.add(
    KeyboardButton(text="Назад🔙"),
    KeyboardButton(text="Добавить автомобиль"),
    KeyboardButton(text="Удалить автомобиль"),

)
auto_settings.adjust(2,2)


add_del_back_menu = ReplyKeyboardBuilder()                          # Клавиатура Добавить/Удалить/Назад
add_del_back_menu.add(
    KeyboardButton(text="Добавить"),
    KeyboardButton(text="Удалить"),
    KeyboardButton(text="Назад🔙"),
)
add_del_back_menu.adjust(2,1)