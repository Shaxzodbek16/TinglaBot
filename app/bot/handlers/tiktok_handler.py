from uuid import uuid4

from app.bot.controller.tiktok_controller import TikTokDownloader
from app.core.extensions.utils import WORKDIR


async def get_tiktok_video(video_url: str) -> str | None:
    download_url = WORKDIR.parent / "media" / "tiktok"
    filename = str(uuid4())
    with TikTokDownloader(headless=True) as downloader:
        return downloader.download_video(video_url, download_url, filename)


def validate_tiktok_url(url: str) -> str:
    base_url = url.split("?")[0].strip().rstrip("/")

    parts = base_url.split("/")
    if len(parts) >= 6 and "tiktok.com" in parts:
        for i in range(len(parts)):
            if parts[i].startswith("@") and i + 2 < len(parts):
                if parts[i + 1] == "video":
                    username = parts[i]
                    video_id = parts[i + 2]
                    return f"https://www.tiktok.com/{username}/video/{video_id}"
    return base_url
