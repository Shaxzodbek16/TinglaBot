from uuid import uuid4

from app.bot.controller.like_controller import LikeeDownloader
from app.core.extensions.utils import WORKDIR


async def download_likee_video_only_mp4(url: str) -> str:
    with LikeeDownloader(headless=True) as downloader:
        video_path = downloader.download_video(
            url, str(uuid4()) + ".mp4", download_path=WORKDIR.parent / "media" / "likee"
        )
        return video_path


def validate_likee_url(url: str) -> str:
    base_url = url.split("?")[0].strip().rstrip("/")
    if "likee.video" in base_url:
        return base_url
    raise ValueError("Invalid Likee video URL")
