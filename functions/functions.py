from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.media_group import MediaGroupBuilder

from database.orm_query import orm_get_admin


async def get_admin_dict(session: AsyncSession) -> dict:
    admin_dict = {}
    admins = await orm_get_admin(session)
    for index, admin in enumerate(admins, start=1):
        admin_dict[index] = {"id": admin.id, "name": admin.name}
    return admin_dict