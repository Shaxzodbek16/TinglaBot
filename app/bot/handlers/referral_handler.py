from sqlalchemy.future import select

from app.bot.models import Referral, AdminRequirements, User
from app.core.databases.postgres import get_general_session
from app.bot.handlers.user_handlers import add_limit_to_user


async def get_referral_by_tg_id(tg_id: int) -> Referral | None:
    async with get_general_session() as session:
        result = await session.execute(select(Referral).where(Referral.tg_id == tg_id))
        return result.scalar_one_or_none()


async def add_referral(tg_id: int, invited_tg_id: int) -> Referral | None:
    if tg_id == invited_tg_id:
        return None
    async with get_general_session() as session:
        result = await session.execute(select(Referral).where(Referral.tg_id == tg_id))
        if result.scalar_one_or_none() is not None:
            return None
        referral = Referral(tg_id=tg_id, invited_tg_id=invited_tg_id)
        session.add(referral)
        admin_q = await session.execute(select(AdminRequirements))
        admin_req = admin_q.scalars().first()
        if admin_req:
            inviter = await session.get(User, invited_tg_id)
            if inviter:
                inviter.limit += admin_req.token_per_referral
                session.add(inviter)
        await session.commit()
        return referral
