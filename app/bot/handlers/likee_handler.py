from uuid import uuid4

from app.bot.controller.like_controller import LikeeDownloader
from app.core.extensions.utils import WORKDIR


# async def download_likee_video_only_mp4(url: str) -> str:
#     with LikeeDownloader(headless=True) as downloader:
#         video_path = downloader.download_video(
#             url, str(uuid4()) + ".mp4", download_path=WORKDIR.parent / "media" / "likee"
#         )
#         return video_path

import subprocess
from uuid import uuid4
from app.core.extensions.utils import WORKDIR


async def download_likee_video_only_mp4(url: str) -> str:
    out_dir = WORKDIR.parent / "media" / "likee"
    out_dir.mkdir(parents=True, exist_ok=True)

    session_dir = out_dir / str(uuid4())
    session_dir.mkdir()

    cmd = ["likeer", "--one", url, "--output", str(session_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise Exception(f"likee-scraper error: {proc.stderr.strip()}")

    files = list(session_dir.glob("*.mp4"))
    if not files:
        raise Exception("No MP4 video found after likee-scraper run.")
    video_path = files[0]

    return str(video_path)


def validate_likee_url(url: str) -> str:
    base_url = url.split("?")[0].strip().rstrip("/")
    if "likee.video" in base_url:
        return base_url
    raise ValueError("Invalid Likee video URL")
