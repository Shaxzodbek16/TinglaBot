from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import os
import time
import re


class TikTokDownloader:
    def __init__(self, headless=True):
        """
        TikTokDownloader orqali TikTok video yuklovchi (Optimized)

        Args:
            headless (bool): Brauzer ko'rinadigan bo'lsin yoki yo'q
        """
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")

        # Tezlashtirish uchun sozlamalar
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-plugins")
        self.options.add_argument("--disable-images")
        # JavaScript kerak, shuning uchun o'chirmaymiz
        # self.options.add_argument('--disable-javascript')
        self.options.add_argument("--disable-css")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--page-load-strategy=normal")

        # Prefs sozlamalari
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        self.options.add_experimental_option("prefs", prefs)

        self.driver = None
        self.wait = None

    def __enter__(self):
        """Context manager enter"""
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.implicitly_wait(5)
        self.wait = WebDriverWait(self.driver, 15)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.driver:
            self.driver.quit()
            print("Brauzer yopildi")

    def _extract_video_id(self, url):
        """URL dan video ID ni ajratib olish"""
        try:
            # TikTok URL dan video ID ni ajratish
            match = re.search(r"/video/(\d+)", url)
            if match:
                return match.group(1)
            return None
        except:
            return None

    def _generate_filename(self, url, custom_name=None):
        """Fayl nomini yaratish"""
        if custom_name:
            # Fayl nomini tozalash
            safe_name = re.sub(r'[<>:"/\\|?*]', "_", custom_name)
            return f"{safe_name}.mp4"

        video_id = self._extract_video_id(url)
        if video_id:
            return f"tiktok_{video_id}.mp4"

        timestamp = str(int(time.time()))
        return f"tiktok_video_{timestamp}.mp4"

    def download_video(self, tiktok_url, save_path=None, filename=None):
        """
        TikTok videosini yuklab olish

        Args:
            tiktok_url (str): TikTok video havolasi
            save_path (str): Saqlash yo'li (default: downloads)
            filename (str): Fayl nomi (default: auto-generated)

        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'filename': str,
                'url': str,
                'download_url': str,
                'error': str or None
            }
        """
        result = {
            "success": False,
            "file_path": None,
            "filename": None,
            "url": tiktok_url,
            "download_url": None,
            "error": None,
        }

        try:
            print(f"🔄 Video yuklanmoqda: {tiktok_url}")

            # Saqlash yo'lini aniqlash
            if save_path is None:
                save_path = "downloads"

            # Papka yaratish
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                print(f"📁 Papka yaratildi: {save_path}")

            # Fayl nomini aniqlash
            result["filename"] = self._generate_filename(tiktok_url, filename)
            result["file_path"] = os.path.join(save_path, result["filename"])

            # SSStiK saytiga o'tish
            print("🌐 SSStiK saytiga kirilmoqda...")
            self.driver.get("https://ssstik.io")

            # Input maydonini topish va URL kiritish
            input_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "main_page_text"))
            )
            input_field.clear()
            input_field.send_keys(tiktok_url)
            print("✅ URL kiritildi")

            # Download tugmasini bosish
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            submit_button.click()
            print("🔄 Jarayonlanmoqda...")

            # "Without watermark" havolasini kutish
            print("🔍 Download tugmalari kutilmoqda...")
            download_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="dl_btns"]/a[1]'))
            )

            # Qo'shimcha kutish - sahifa to'liq yuklanishi uchun
            time.sleep(2)

            # Download havola URLni olish
            download_url = download_link.get_attribute("href")
            result["download_url"] = download_url
            print(f"🔗 Download havola topildi: {download_url[:50]}...")

            # URL ni tekshirish
            if not download_url or download_url == "javascript:void(0)":
                raise Exception("Download havola noto'g'ri yoki topilmadi")

            # Faylni yuklab olish
            print("⬇️ Fayl yuklanmoqda...")

            # Headers qo'shish
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://ssstik.io/",
                "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
            }

            response = requests.get(
                download_url, stream=True, headers=headers, timeout=30
            )
            response.raise_for_status()

            # Content-Length tekshirish
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) == 0:
                raise Exception("Fayl bo'sh (0 KB)")

            print(f"📊 Fayl hajmi: {content_length} byte")

            # Faylni saqlash
            with open(result["file_path"], "wb") as f:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(
                                f"\r📥 Yuklanmoqda: {progress:.1f}%", end="", flush=True
                            )

            print(f"\n✅ Video muvaffaqiyatli yuklandi!")
            print(f"📁 Fayl yo'li: {result['file_path']}")
            print(f"📝 Fayl nomi: {result['filename']}")

            result["success"] = True
            return result

        except TimeoutException:
            error_msg = "Sahifa yuklashda vaqt tugadi"
            print(f"❌ Xatolik: {error_msg}")
            result["error"] = error_msg

        except requests.RequestException as e:
            error_msg = f"Fayl yuklab olishda xatolik: {str(e)}"
            print(f"❌ Xatolik: {error_msg}")
            result["error"] = error_msg

        except WebDriverException as e:
            error_msg = f"Brauzer xatoligi: {str(e)}"
            print(f"❌ Xatolik: {error_msg}")
            result["error"] = error_msg

        except Exception as e:
            error_msg = f"Kutilmagan xatolik: {str(e)}"
            print(f"❌ Xatolik: {error_msg}")
            result["error"] = error_msg

        return result


# Context manager bilan foydalanish
def download_tiktok_video(url, save_path=None, filename=None, headless=True):
    """
    TikTok videosini yuklab olish (yengil funksiya)

    Args:
        url (str): TikTok video havolasi
        save_path (str): Saqlash yo'li
        filename (str): Fayl nomi
        headless (bool): Headless rejim

    Returns:
        dict: Download natijalari
    """
    with SSStiKDownloader(headless=headless) as downloader:
        return downloader.download_video(url, save_path, filename)


# Foydalanish misoli
def main():
    # URL kiritish
    tiktok_url = input("TikTok video URL kiriting: ").strip()

    if not tiktok_url:
        print("❌ URL kiritilmadi!")
        return

    # Saqlash yo'li (ixtiyoriy)
    save_path = input("Saqlash papkasi (Enter - default 'downloads'): ").strip()
    if not save_path:
        save_path = None

    # Fayl nomi (ixtiyoriy)
    filename = input("Fayl nomi (Enter - avtomatik): ").strip()
    if not filename:
        filename = None

    # Context manager bilan download
    print("\n" + "=" * 50)
    result = download_tiktok_video(
        url=tiktok_url,
        save_path=save_path,
        filename=filename,
        headless=False,  # Ko'rinadigan rejim
    )

    print("=" * 50)

    # Natijani ko'rsatish
    if result["success"]:
        print("🎉 MUVAFFAQIYATLI!")
        print(f"📱 URL: {result['url']}")
        print(f"📁 Saqlangan joy: {result['file_path']}")
        print(f"📝 Fayl nomi: {result['filename']}")
        print(f"🔗 Download URL: {result['download_url']}")
    else:
        print("❌ MUVAFFAQIYATSIZ!")
        print(f"📱 URL: {result['url']}")
        print(f"🚫 Xatolik: {result['error']}")


if __name__ == "__main__":
    main()
