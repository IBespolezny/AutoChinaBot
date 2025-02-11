from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import text
from aiogram.utils.media_group import MediaGroupBuilder

from database.models import Base
from database.orm_query import orm_get_admin, orm_get_admins, orm_get_managers


async def get_admin_dict(session: AsyncSession) -> dict:
    admin_dict = {}
    admins = await orm_get_admin(session)
    for index, admin in enumerate(admins, start=1):
        admin_dict[index] = {"id": admin.id, "name": admin.name}
    return admin_dict


async def create_specific_table(engine: AsyncEngine, table: Base):
    """
    Создаёт таблицу, если она отсутствует.
    """
    table_name = table.__tablename__

    try:
        async with engine.connect() as conn:
            query = text(
                f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table_name}';"
            )
            result = await conn.execute(query)
            table_exists = result.scalar() > 0

            if not table_exists:
                # Создаём таблицу, если она отсутствует
                async with engine.begin() as sync_conn:
                    await sync_conn.run_sync(table.metadata.create_all)
                print(f"Таблица '{table_name}' создана.")
            else:
                print(f"Таблица '{table_name}' уже существует.")
    except Exception as e:
        print(f"Ошибка при создании таблицы {table_name}: {e}")


def format_number(value):
    if not isinstance(value, (int, float)):
        raise ValueError("Входное значение должно быть int или float")
    
    if isinstance(value, float):
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{value:,}".replace(",", " ")



async def get_admins_and_managers(session: AsyncSession):
    admins = await orm_get_admins(session)  # Получение админов из БД
    managers = await orm_get_managers(session)  # Получение менеджеров из БД

    adminss = {admin.id: admin.name for admin in admins}
    managerss = {manager.id: manager.name for manager in managers}

    admins_ids = list(adminss.keys())
    managers_ids = list(managerss.keys())

    return admins_ids, adminss, managers_ids, managerss