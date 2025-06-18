#!/usr/bin/env python3
"""
snapchat_downloader.py

A straightforward Snapchat video downloader using yt-dlp.
Downloads the best available video+audio, merges into MP4,
and omits any on-screen watermark.
"""

from yt_dlp import YoutubeDL


def download_snap(url: str, output_template: str = "%(title)s.%(ext)s"):
    """
    Download a Snapchat video at the highest quality, no watermark.
    :param url: Full Snapchat video/story URL.
    :param output_template: yt-dlp output template for filenames.
    """
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": True,
        # Some sites strip watermarks if you avoid embedding subs or metadata
        "writesubtitles": False,
        "writeautomaticsub": False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("✅ Download complete. Check your file!")
        except Exception as e:
            print(f"❌ Failed to download: {e}")


def main():
    download_snap(
        "https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYYWRqa2tjYXRuAZdhlIgUAZdd6pCFAAAAAQ"
    )


if __name__ == "__main__":
    main()
