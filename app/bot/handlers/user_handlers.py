from aiogram.types import Message

from app.bot.models import User
from app.core.databases.postgres import get_general_session
from sqlalchemy.future import select


async def get_user_by_tg_id(tg_id: int) -> User | None:
    async with get_general_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        return user.scalar_one_or_none()


async def update_user_by_tg_id(tg_id, data: dict) -> User:
    async with get_general_session() as session:
        user = await get_user_by_tg_id(tg_id)
        if not user:
            user = User(tg_id=tg_id, **data)
            session.add(user)
        else:
            user.update(**data)
            session.add(user)
        await session.commit()
        return user


async def update_user_by_message(message: Message) -> User:
    data = {
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "username": message.from_user.username,
        "is_tg_premium": (
            message.from_user.is_premium if message.from_user.is_premium else False
        ),
    }
    return await update_user_by_tg_id(message.from_user.id, data)


async def create_user(message: Message) -> User:
    async with get_general_session() as session:
        existing_user = await get_user_by_tg_id(message.from_user.id)
        if existing_user:
            await update_user_by_message(message)
            return existing_user
        user = User(
            tg_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            is_tg_premium=(
                message.from_user.is_premium if message.from_user.is_premium else False
            ),
        )
        session.add(user)
        await session.commit()
        return user


async def add_limit_to_user(tg_id: int, limit: int) -> User:
    async with get_general_session() as session:
        user = await get_user_by_tg_id(tg_id)
        user.limit += limit
        session.add(user)
        await session.commit()
        return user


async def remove_limit_from_user(tg_id: int, limit: int) -> User:
    """
    Removes a specified limit from a user's current limit.

    This asynchronous function modifies a user's account by reducing their set limit
    by a given amount. If the user has no limit or the reduction amount exceeds the
    current limit, a ValueError is raised.

    Args:
        tg_id (int): The Telegram ID of the user.
        limit (int): The limit amount to be removed.

    Returns:
        User: The updated user object after the limit is reduced.

    Raises:
        ValueError: If the user has no limit to remove or if the reduction amount
        exceeds the user's current limit.
    """
    async with get_general_session() as session:
        user = await get_user_by_tg_id(tg_id)
        if user.limit == 0:
            raise ValueError("User has no limit to remove")
        if user.limit < limit:
            raise ValueError("Insufficient limit")
        user.limit -= limit
        session.add(user)
        await session.commit()
        return user
