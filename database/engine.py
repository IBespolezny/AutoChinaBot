import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from functions.functions import get_admin_dict

# from functions import get_admin_dict

engine = create_async_engine(config.DB_POSTGRE, echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def initialize_admins():
    async with session_maker() as session:  # Создаем асинхронную сессию с использованием созданного session_maker
        admins = await get_admin_dict(session)  # Получаем словарь админов
        return admins