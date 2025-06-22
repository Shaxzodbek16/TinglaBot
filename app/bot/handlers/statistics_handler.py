from sqlalchemy.future import select

from app.bot.models import Statistics
from app.core.databases.postgres import get_general_session


async def get_statistics_by_tg_id(tg_id: int) -> Statistics | None:
    async with get_general_session() as session:
        query = select(Statistics).where(Statistics.tg_id == tg_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def create_statistics(
    tg_id: int,
) -> Statistics:
    statistics = Statistics(
        tg_id=tg_id,
    )
    async with get_general_session() as session:
        session.add(statistics)
        await session.commit()
        return statistics


async def update(tg_id: int, **kwargs) -> Statistics:
    """
    Fields:
    - user_id: ID of the user
    - from_text: Count of text messages sent by the user
    - from_voice: Count of voice messages sent by the user
    - from_youtube: Count of YouTube links shared by the user
    - from_tiktok: Count of TikTok links shared by the user
    - from_like: Count of likes given by the user
    - from_snapchat: Count of Snapchat links shared by the user
    - from_instagram: Count of Instagram links shared by the user
    - from_twitter: Count of Twitter links shared by the user
    """
    statistics = await get_statistics_by_tg_id(tg_id)
    if not statistics:
        statistics = await create_statistics(tg_id)
    statistics.add_one(**kwargs)
    async with get_general_session() as session:
        session.add(statistics)
        await session.commit()
        return statistics
