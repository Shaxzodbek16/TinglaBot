#!/usr/bin/env python3
import uuid

from yt_dlp import YoutubeDL


def download_pin(url: str, output_template: str):
    ydl_opts = {
        "format": "best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("✅ Pin downloaded successfully.")
        except Exception as e:
            print(f"❌ Download error: {e}")


def main():
    download_pin("https://pin.it/3oOXpvEKZ", str(uuid.uuid4().hex) + ".%(ext)s")


if __name__ == "__main__":
    main()
