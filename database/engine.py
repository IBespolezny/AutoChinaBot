from dotenv import load_dotenv
import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import os
from database.models import Base
from functions.functions import get_admin_dict

# Загружаем переменные окружения из .env файла
load_dotenv()

# Считываем параметры подключения из переменных окружения
POSTGRES_USER = os.getenv("POSTGRES_USER", "default_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "default_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "default_db")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")

# Формируем строку подключения
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{PG_HOST}:{PG_PORT}/{POSTGRES_DB}"

# Проверяем строку подключения
if not DATABASE_URL:
    raise ValueError("Database URL could not be constructed. Check your environment variables.")
engine = create_async_engine(DATABASE_URL, echo=True)

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