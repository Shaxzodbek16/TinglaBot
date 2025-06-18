from faker import Faker

from app.core.databases.postgres import get_general_session
from app.bot.models import Channel


async def create_channels() -> list[Channel]:
    async with get_general_session() as session:
        fake = Faker()
        channels = []
        for _ in range(10):
            channel = Channel(
                name=fake.name(),
                link=fake.url(),
                channel_id=fake.random_int(min=1000000000, max=9999999999) * -1,
                is_active=fake.boolean(),
            )
            session.add(channel)
            channels.append(channel)
        await session.commit()
        return channels


async def main():
    await create_channels()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
