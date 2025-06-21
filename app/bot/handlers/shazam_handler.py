from shazamio import Shazam

shazam = Shazam()


async def find_music_by_text(text: str) -> list:
    result = await shazam.search_track(text)
    return result["tracks"]["hits"]


async def main():
    songs = await find_music_by_text("blinding lights")
    for song in songs:
        url = song["stores"]["apple"]["previewurl"]


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
