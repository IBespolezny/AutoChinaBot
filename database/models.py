from sqlalchemy import DateTime, String, func
from sqlalchemy import BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class Admin(Base):
    __tablename__ = 'admin'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class Manager(Base):
    __tablename__ = 'manager'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class DefQuestion(Base):
    __tablename__ = 'default_question'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(400), nullable=False)
    answer: Mapped[str] = mapped_column(String(1000), nullable=False)


class Dialog(Base):
    __tablename__ = 'dialog'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[BIGINT] = mapped_column(BIGINT, nullable=False)
    client_message_id: Mapped[int] = mapped_column(nullable=False)
    manager_id: Mapped[BIGINT] = mapped_column(BIGINT, nullable=True)
    manager_message_id: Mapped[int | None] = mapped_column(nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)



class Cars(Base):
    __tablename__ = 'cars'

    car_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mark: Mapped[str] = mapped_column(String(150), nullable=False)
    model: Mapped[str] = mapped_column(String(150), nullable=False)
    package: Mapped[str] = mapped_column(String(150), nullable=False)   # Комплектакция
    body: Mapped[str] = mapped_column(String(150), nullable=False)   # Кузов
    year: Mapped[int] = mapped_column(nullable=False)
    cost: Mapped[float] = mapped_column(nullable=False)
    engine_type: Mapped[str] = mapped_column(String(150), nullable=False)    # Тип топлива
    weel_drive: Mapped[str] = mapped_column(String(150), nullable=False)    # Привод
    flag: Mapped[str] = mapped_column(String(150), nullable=False)              # Флаг для поиска в БД
    electrocar: Mapped[str] = mapped_column(String(300), nullable=False)     # Электромобиль?
    engine_volume: Mapped[float] = mapped_column(nullable=True)            # Объём двигателя (только ДВС)
    power: Mapped[float] = mapped_column(nullable=False)                     # Мощность (только для электрокаров) 
    power_bank: Mapped[float] = mapped_column(nullable=True)                # Батарея (только для электрокаров) 
    power_reserve: Mapped[float] = mapped_column(nullable=True)                # Батарея (только для электрокаров) 
    route: Mapped[float] = mapped_column(nullable=False)                     # Пробег или запас хода (ДВС)_(электрокар)
    photo: Mapped[str] = mapped_column(String(300), nullable=False)            # Фото
    
    

class ManagersGroup(Base):
    __tablename__ = 'managers_group'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[BIGINT] = mapped_column(BIGINT, nullable=False)