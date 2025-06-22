from aiogram.types import Message

from app.bot.handlers.admin import get_token_per_referral
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


async def create_user(message: Message, ref_id: int | None = None) -> User:
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
            referred_by=ref_id,
        )
        session.add(user)
        await session.commit()
        return user


async def get_referral_count(tg_id: int) -> int:
    async with get_general_session() as session:
        result = await session.execute(select(User).where(User.referred_by == tg_id))
        return len(result.scalars().all())
