import yt_dlp


def download_tiktok_video(url):
    options = {
        "outtmpl": "%(title)s.%(ext)s",
        "format": "best",
        "noplaylist": True,
        "quiet": False,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        try:
            ydl.download([url])
            print("✅ Video yuklab olindi:", url)
        except Exception as e:
            print("❌ Xatolik yuz berdi:", e)


if __name__ == "__main__":
    urls = [
        "https://www.tiktok.com/@tomjerry_moments/video/7513756585085226262?is_from_webapp=1&sender_device=pc",
    ]

    for url in urls:
        download_tiktok_video(url)
