import os
import re
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import select, text


from database.models import Base, CalculateAuto
from database.orm_query import orm_get_admin, orm_get_admins, orm_get_car, orm_get_managers



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


def int_format(value):
    new_value = int(value)
    return f"{new_value:,}".replace(",", " ")


async def get_admins_and_managers(session: AsyncSession):
    admins = await orm_get_admins(session)  # Получение админов из БД
    managers = await orm_get_managers(session)  # Получение менеджеров из БД

    adminss = {admin.id: admin.name for admin in admins}
    managerss = {manager.id: manager.name for manager in managers}

    admins_ids = list(adminss.keys())
    managers_ids = list(managerss.keys())

    return admins_ids, adminss, managers_ids, managerss


def is_valid_phone_number(phone: str) -> bool:
    """Проверяет, введён ли номер в международном формате (+код страны и цифры)."""
    if not phone:  # Проверка на пустую строку
        return False

    phone = phone.strip()  # Убираем лишние пробелы в начале и конце

    pattern = r"^\+\d{10,15}$"  # Международный формат +код и от 10 до 15 цифр
    match = re.match(pattern, phone)

    return match is not None  # Вернёт True, если формат правильный


async def create_calculate_table_with_defaults(engine: AsyncEngine):
    """
    Создаёт таблицу calculate_auto, если она отсутствует, и добавляет запись с дефолтными значениями, если таблица пуста.
    """
    try:
        async with engine.connect() as conn:
            # Проверяем, существует ли таблица
            query = text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'calculate_auto';"
            )
            result = await conn.execute(query)
            table_exists = result.scalar() > 0

            if not table_exists:
                # Создаём таблицу
                async with engine.begin() as sync_conn:
                    await sync_conn.run_sync(CalculateAuto.metadata.create_all)
                print("Таблица 'calculate_auto' создана.")

            # Проверяем, есть ли запись в таблице
            async with AsyncSession(engine) as session:
                query = select(CalculateAuto)
                result = await session.execute(query)
                record_exists = result.scalars().first()

                if not record_exists:
                    # Добавляем запись с дефолтными значениями
                    default_record = CalculateAuto(
                        min_cost=5000.0,
                        custom=500.0,
                        comis_rb=24.0,
                        bank_comis=2.0,
                        delivery=2300.0,
                        engine_volume_1500=1750.0,
                        engine_volume_1500_1800=3000.0,
                        engine_volume_1800_2300=3800.0,
                    )
                    session.add(default_record)
                    await session.commit()
                    print("Запись с дефолтными значениями добавлена в таблицу 'calculate_auto'.")
                else:
                    print("В таблице 'calculate_auto' уже существует запись.")
    except Exception as e:
        print(f"Ошибка при создании таблицы calculate_auto: {e}")