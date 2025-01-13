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
    manager_id: Mapped[int | None] = mapped_column(nullable=True, default=None)
    manager_message_id: Mapped[int | None] = mapped_column(nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)

