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

        # Headless mode sozlamalari
        if headless:
            self.options.add_argument("--headless")

        # Umumiy sozlamalar
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-plugins")

        # Non-headless mode uchun rasmlarni o'chirmaslik
        if headless:
            self.options.add_argument("--disable-images")

        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--page-load-strategy=normal")

        # User agent qo'shish
        self.options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Bot detection oldini olish
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)

        # Prefs sozlamalari - headless mode uchungina
        if headless:
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

        # Bot detection oldini olish
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Implicit wait o'rnatish
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 30)  # Timeout ni oshirish
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

            # Sahifa to'liq yuklanishini kutish
            time.sleep(3)

            # Input maydonini topish va URL kiritish
            print("🔍 Input maydonini qidirilmoqda...")

            # Bir nechta selector bilan urinish
            input_selectors = [
                (By.ID, "main_page_text"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[placeholder*='URL']"),
                (By.CSS_SELECTOR, "textarea"),
                (By.CSS_SELECTOR, "#main_page_text"),
            ]

            input_field = None
            for selector_type, selector_value in input_selectors:
                try:
                    input_field = self.wait.until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"✅ Input maydon topildi: {selector_value}")
                    break
                except TimeoutException:
                    print(
                        f"⚠️  {selector_value} topilmadi, keyingisini sinab ko'ramiz..."
                    )
                    continue

            if not input_field:
                raise Exception("Input maydoni topilmadi")

            # URL kiritish
            input_field.clear()
            time.sleep(1)  # Qisqa kutish
            input_field.send_keys(tiktok_url)
            print("✅ URL kiritildi")

            time.sleep(2)  # URL kiritishdan keyin kutish

            # Submit tugmasini topish va bosish
            print("🔍 Submit tugmasini qidirilmoqda...")

            submit_selectors = [
                (By.ID, "submit"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.CSS_SELECTOR, "button"),
                (By.XPATH, "//button[contains(text(), 'Download')]"),
                (By.XPATH, "//input[@value='Download']"),
            ]

            submit_button = None
            for selector_type, selector_value in submit_selectors:
                try:
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    print(f"✅ Submit tugma topildi: {selector_value}")
                    break
                except TimeoutException:
                    print(
                        f"⚠️  {selector_value} topilmadi, keyingisini sinab ko'ramiz..."
                    )
                    continue

            if not submit_button:
                raise Exception("Submit tugmasi topilmadi")

            # Tugmani bosish
            self.driver.execute_script("arguments[0].click();", submit_button)
            print("🔄 Jarayonlanmoqda...")

            # Download tugmalarini kutish
            print("🔍 Download tugmalari kutilmoqda...")

            # Bir nechta download selector
            download_selectors = [
                (By.XPATH, '//*[@id="dl_btns"]/a[1]'),
                (By.CSS_SELECTOR, "#dl_btns a:first-child"),
                (By.XPATH, "//a[contains(text(), 'Without watermark')]"),
                (By.CSS_SELECTOR, "a[href*='.mp4']"),
                (By.XPATH, "//a[contains(@href, 'download')]"),
            ]

            download_link = None
            max_wait = 45  # Maksimal kutish vaqti
            start_time = time.time()

            while time.time() - start_time < max_wait:
                for selector_type, selector_value in download_selectors:
                    try:
                        download_link = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        print(f"✅ Download havola topildi: {selector_value}")
                        break
                    except TimeoutException:
                        continue

                if download_link:
                    break

                print("⏳ Download tugmalari kutilmoqda...")
                time.sleep(3)

            if not download_link:
                raise Exception("Download tugmalari topilmadi")

            # Download havola URLni olish
            download_url = download_link.get_attribute("href")
            result["download_url"] = download_url
            print(f"🔗 Download havola topildi: {download_url[:50]}...")

            # URL ni tekshirish
            if (
                not download_url
                or download_url == "javascript:void(0)"
                or "javascript:" in download_url
            ):
                raise Exception("Download havola noto'g'ri yoki topilmadi")

            # Faylni yuklab olish
            print("⬇️ Fayl yuklanmoqda...")

            # Headers qo'shish
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://ssstik.io/",
                "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            response = requests.get(
                download_url, stream=True, headers=headers, timeout=60
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
            error_msg = "Sahifa yuklashda vaqt tugadi (timeout)"
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
