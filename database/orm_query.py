from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Admin, Cars, DefQuestion, Dialog, Manager

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
    obj = Dialog(
        client_id=client_id,
        client_message_id=client_message_id,
        manager_id=None,  # Явное указание NULL
        manager_message_id=None,  # Явное указание NULL
        is_active=True
    )
    session.add(obj)
    await session.commit()


    
async def orm_get_dialog_by_client_message(session: AsyncSession, client_message_id: int) -> Dialog | None:
    query = select(Dialog).where(Dialog.client_message_id == client_message_id, Dialog.is_active == True)
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




async def orm_end_dialog(session: AsyncSession, client_id: int | None = None, manager_id: int | None = None):   # Заканчивает диалог с клиентом
    query = (
        select(Dialog)
        .where(Dialog.is_active == True)
    )
    if client_id:
        query = query.where(Dialog.client_id == client_id)
    if manager_id:
        query = query.where(Dialog.manager_id == manager_id)
    result = await session.execute(query)
    dialogs = result.scalars().all()
    for dialog in dialogs:
        dialog.is_active = False
    await session.commit()



async def orm_save_client_message(
    session: AsyncSession,
    client_id: int,
    manager_id: int,
    client_message_id: int,
    manager_message_id: int
) -> None:
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
        year=new_car["year"],
        engine_volume=new_car["engine_volume"],
        places=new_car["places"],
        route=new_car["route"],
        engine_type=new_car["engine_type"],
        box=new_car["box"],
        foto=new_car["foto"],
        electrocar=new_car["electrocar"],
        cost=new_car["cost"],
        flag=new_car["flag"],
    )
    session.add(obj)
    await session.commit()


async def orm_get_car(session: AsyncSession, car_id: int):             # Получение одного вопроса по id
    query = select(Cars).where(Cars.car_id == car_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_car_by_flag(session: AsyncSession, flag: str):             # Получение одного вопроса по id
    query = select(Cars).where(Cars.flag == flag)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_electrocars(session: AsyncSession):             # Получение одного вопроса по id
    query = select(Cars).where(Cars.electrocar == "Да")
    result = await session.execute(query)
    return result.scalars().all()