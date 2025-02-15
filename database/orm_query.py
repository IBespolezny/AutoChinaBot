from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Admin, Cars, DefQuestion, Dialog, Manager, ManagersGroup

##############################   АДМИНИСТРАТОРЫ   #######################################

async def orm_add_admin(session: AsyncSession, new_admin_dict: dict):       # Добавление администратора
    obj = Admin(
        id=new_admin_dict["id"],
        name=new_admin_dict["name"]
    )
    session.add(obj)
    await session.commit()



async def orm_get_admins(session: AsyncSession):                             # Получение всех администраторов
    query = select(Admin)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_admin(session: AsyncSession, Admin_id: int):             # Получение одного администратора по id
    query = select(Admin).where(Admin.id == Admin_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_admin(session: AsyncSession, Admin_id: int):           # Удаление одного администратора
    query = delete(Admin).where(Admin.id == Admin_id)
    await session.execute(query)
    await session.commit()




##############################   Менеджеры   #######################################

async def orm_add_manager(session: AsyncSession, new_manager_dict: dict):     # Добавление менеджера
    obj = Manager(
        id=new_manager_dict["id"],
        name=new_manager_dict["name"]
    )
    session.add(obj)
    await session.commit()



async def orm_get_managers(session: AsyncSession):                             # Получение всех менеджеров
    query = select(Manager)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_manager(session: AsyncSession, Manager_id: int):           # Получение одного менеджера по id
    query = select(Manager).where(Manager.id == Manager_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_manager(session: AsyncSession, Manager_id: int):         # Удаление одного менеджера по id
    query = delete(Manager).where(Manager.id == Manager_id)
    await session.execute(query)
    await session.commit()





##############################   Частые вопросы   #######################################

async def orm_add_DefQuestion(session: AsyncSession, new_default_question: dict):     # Добавление частого вопроса
    obj = DefQuestion(
        question=new_default_question["question"],
        answer=new_default_question["answer"]
    )
    session.add(obj)
    await session.commit()


async def orm_get_DefQuestions(session: AsyncSession):                             # Получение всех частых вопросов
    query = select(DefQuestion)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_DefQuestion(session: AsyncSession, Question_id: int):             # Получение одного вопроса по id
    query = select(DefQuestion).where(DefQuestion.id == Question_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_DefQuestion(session: AsyncSession, Question_id: int):         # Удаление одного вопроса по id
    query = delete(DefQuestion).where(DefQuestion.id == Question_id)
    await session.execute(query)
    await session.commit()





##############################   Диалоги с клиентом   #######################################

async def orm_add_dialog(session: AsyncSession, client_id: int, client_message_id: int):
    """Добавляет новый диалог или обновляет существующий."""
    query = select(Dialog).where(Dialog.client_id == client_id)
    result = await session.execute(query)
    dialog = result.scalar()

    if dialog:
        # Если запись уже есть, обновляем client_message_id и обнуляем менеджера
        dialog.client_message_id = client_message_id
        dialog.manager_id = None
        dialog.manager_message_id = None
    else:
        # Если записи нет, создаем новую
        dialog = Dialog(
            client_id=client_id,
            client_message_id=client_message_id,
            manager_id=None,  # Явное указание NULL
            manager_message_id=None,  # Явное указание NULL
            is_active=True
        )
        session.add(dialog)

    await session.commit()



    
async def orm_get_dialog_by_client_message(session: AsyncSession, client_message_id: int) -> Dialog | None:
    query = select(Dialog).where(Dialog.client_message_id == client_message_id, Dialog.is_active == True)
    result = await session.execute(query)  # Ожидание выполнения запроса
    dialog = result.scalar()  # Извлечение одной записи (или None)
    return dialog


async def orm_get_dialog_by_client_id(session: AsyncSession, client_id: int) -> Dialog | None:
    query = select(Dialog).where(Dialog.client_id == client_id, Dialog.is_active == True)
    result = await session.execute(query)  # Ожидание выполнения запроса
    dialog = result.scalar()  # Извлечение одной записи (или None)
    return dialog


async def orm_update_manager_in_dialog(session: AsyncSession, client_message_id: int, manager_id: int | None, manager_message_id: int | None):     # Обновляет данные диалога
    query = (
        select(Dialog)
        .where(Dialog.client_message_id == client_message_id, Dialog.is_active == True)
    )
    result = await session.execute(query)
    dialog = result.scalar()

    if dialog:
        if manager_id is not None:
            dialog.manager_id = manager_id
        if manager_message_id is not None:
            dialog.manager_message_id = manager_message_id
        await session.commit()




async def orm_end_dialog(session: AsyncSession, client_id: int | None = None, manager_id: int | None = None):
    """Удаляет диалог с клиентом из базы данных."""
    query = select(Dialog).where(Dialog.is_active == True)

    if client_id:
        query = query.where(Dialog.client_id == client_id)
    if manager_id:
        query = query.where(Dialog.manager_id == manager_id)

    result = await session.execute(query)
    dialogs = result.scalars().all()

    if dialogs:
        for dialog in dialogs:
            await session.delete(dialog)  # Удаляем найденные записи
        await session.commit()  # Фиксируем изменения в БД




async def orm_save_client_message(
    session: AsyncSession,
    client_id: int,
    manager_id: int,
    client_message_id: int,
    manager_message_id: int
) -> None:
    """Сохраняет сообщение клиента, обновляя существующую запись или создавая новую."""
    query = select(Dialog).where(Dialog.client_id == client_id)
    result = await session.execute(query)
    dialog = result.scalar()

    if dialog:
        # Если запись уже есть, обновляем данные
        dialog.client_message_id = client_message_id
        dialog.manager_id = manager_id
        dialog.manager_message_id = manager_message_id
    else:
        # Если записи нет, создаем новую
        new_message = Dialog(
            client_id=client_id,
            manager_id=manager_id,
            client_message_id=client_message_id,
            manager_message_id=manager_message_id,
            is_active=True  # Обозначаем, что диалог активен
        )
        session.add(new_message)

    await session.commit()




async def orm_delete_all_dialogs(session: AsyncSession) -> None:       # Удаляет все записи из таблицы Dialog
    query = delete(Dialog)  # Создаем запрос на удаление всех записей из таблицы Dialog
    await session.execute(query)  # Выполняем запрос
    await session.commit()  # Подтверждаем изменения



####################################### Добавление авто ################################

async def orm_add_car(session: AsyncSession, new_car: dict):     # Добавление частого вопроса
    obj = Cars(
        mark=new_car["mark"],
        model=new_car["model"],
        package=new_car["package"],
        year=new_car["year"],
        cost=new_car["cost"],
        engine_type=new_car["engine_type"],
        weel_drive=new_car["weel_drive"],
        flag=new_car["flag"],
        electrocar=new_car["electrocar"],
        engine_volume=new_car["engine_volume"],
        power=new_car["power"],
        power_bank=new_car["power_bank"],
        route=new_car["route"],
        photo=new_car["photo"],
        body=new_car["body"],
        power_reserve=new_car["power_reserve"],
    )
    session.add(obj)
    await session.commit()


async def orm_get_car(session: AsyncSession, car_id: int):             # Получение одного вопроса по id
    query = select(Cars).where(Cars.car_id == car_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_cars(session: AsyncSession):
    """Получение всех автомобилей из базы."""
    query = select(Cars.car_id, Cars.mark, Cars.model, Cars.cost)
    result = await session.execute(query)
    return result.fetchall()


async def orm_get_car_by_flag(session: AsyncSession, flag: str):             # Получение одного вопроса по id
    query = select(Cars).where(Cars.flag == flag)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_electrocars(session: AsyncSession):             # Получение одного вопроса по id
    query = select(Cars).where(Cars.electrocar == "yes")
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_cars_by_cost(session: AsyncSession, min_value: float, max_value: float):
    """Получение списка автомобилей в заданном диапазоне цен."""
    query = select(Cars).where(Cars.cost.between(min_value, max_value))
    result = await session.execute(query)
    cars = result.scalars().all()
    
    return cars


################### Удаление авто ##########################

async def orm_delete_car(session: AsyncSession, car_id: int) -> bool:
    """Удаляет автомобиль из базы данных по его ID."""
    try:
        await session.execute(delete(Cars).where(Cars.car_id == car_id))
        await session.commit()
        return True
    except SQLAlchemyError:
        await session.rollback()
        return False
    



######################## Группа с админами #######################

async def orm_update_managers_group(session: AsyncSession, group_id: int):
    """
    Обновляет единственную запись в таблице ManagersGroup на новую с указанным group_id.
    Если запись отсутствует, создается новая.
    """

    # Получаем существующую запись (она должна быть одна)
    query = select(ManagersGroup)
    result = await session.execute(query)
    existing_record = result.scalars().first()

    if existing_record:
        # Обновляем существующую запись
        existing_record.group_id = group_id
    else:
        # Создаем новую запись, если её нет
        new_record = ManagersGroup(group_id=group_id)
        session.add(new_record)

    # Сохраняем изменения
    await session.commit()



async def orm_get_managers_group(session: AsyncSession):
    """
    Получает все записи о сообщениях из базы данных.
    """
    query = select(ManagersGroup)
    result = await session.execute(query)
    group = result.scalars().first()
    if group:
        return group.group_id
    else:
        return None