import pyktok as pyk

class TikTokDownloader:
    def __init__(self, download_path: str):
        self.download_path = download_path

    def download_video(self, video_url: str, custom_name: str = None) -> str:
        pyk.save_tiktok(video_url, save_video=True)
