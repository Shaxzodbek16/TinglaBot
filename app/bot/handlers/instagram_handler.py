from instaloader import Instaloader, Post
from uuid import uuid4

from app.core.extensions.utils import WORKDIR


async def download_instagram_video_only_mp4(url: str) -> str:
    filename = str(uuid4())
    loader = Instaloader(
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
        filename_pattern=filename,
    )

    shortcode = url.strip("/").split("/")[-1]
    post = Post.from_shortcode(loader.context, shortcode)

    target_folder = WORKDIR.parent / "media" / "instagram"
    loader.download_post(post, target=target_folder)

    return str(target_folder / filename) + ".mp4"


def validate_instagram_url(url: str) -> str:
    base_url = url.split("?")[0].strip().rstrip("/")

    parts = base_url.split("/")
    if len(parts) >= 5 and "instagram.com" in parts:
        for i in range(len(parts)):
            if parts[i] in ["reel", "reels"] and i + 1 < len(parts):
                reel_id = parts[i + 1]
                return f"https://www.instagram.com/reel/{reel_id}/"
    return base_url
