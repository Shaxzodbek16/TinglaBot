import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import os
import re


class LikeeDownloader:
    def __init__(self, headless=True):
        self.driver = None
        self.setup_driver(headless)

    def setup_driver(self, headless=True):
        chrome_options = Options()

        if headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--disk-cache-size=0")
        chrome_options.add_argument("--disable-infobars")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")
        # DON'T disable JavaScript - the site needs it to work
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            raise

    def download_video(self, likee_url, filename=None, download_path="./downloads/"):
        try:
            start_time = time.time()
            os.makedirs(download_path, exist_ok=True)

            # Generate filename if not provided
            if not filename:
                # Extract video ID from URL if possible
                video_id = re.search(r"/v/([^/?]+)", likee_url)
                if video_id:
                    filename = f"likee_{video_id.group(1)}.mp4"
                else:
                    filename = f"likee_video_{int(time.time())}.mp4"

            print(f"Starting download for: {likee_url}")

            # Navigate to the downloader site
            self.driver.get("https://likeedownloader.com/")
            time.sleep(2)  # Wait for page to fully load

            input_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "main_page_text"))
            )

            download_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[@id='main_page_form']/div/span/button")
                )
            )

            input_field.clear()
            time.sleep(0.5)
            input_field.send_keys(likee_url)
            time.sleep(1)

            # Click download button
            download_button.click()
            print("Processing video... Please wait.")

            # Wait for results to appear - try multiple possible selectors
            download_link = None
            selectors_to_try = [
                '//*[@id="results"]/div/div[3]/div[2]/div[2]/a',
                '//a[contains(@class, "download_link")]',
                '//a[contains(@class, "without_watermark")]',
                '//a[contains(text(), "Download")]',
            ]

            for selector in selectors_to_try:
                try:
                    download_link = WebDriverWait(self.driver, 35).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"Found download link with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not download_link:
                print("❌ Could not find download link")
                return None

            # Scroll to the element and get the URL
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", download_link
            )
            time.sleep(1)

            download_url = download_link.get_attribute("href")

            if not download_url or download_url == "#":
                print("❌ Invalid download URL")
                return None

            print(f"Download URL obtained: {download_url[:80]}...")

            # Download the file with proper headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://likeedownloader.com/",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "Upgrade-Insecure-Requests": "1",
            }

            session = requests.Session()

            # First make a HEAD request to check if the URL is valid
            try:
                head_response = session.head(
                    download_url, headers=headers, timeout=10, allow_redirects=True
                )
                print(f"HEAD request status: {head_response.status_code}")
                if head_response.status_code == 404:
                    print("❌ Video file not found (404)")
                    return None
            except Exception as e:
                print(f"HEAD request failed: {e}")

            # Now download the actual file
            response = session.get(
                download_url,
                headers=headers,
                stream=True,
                timeout=60,
                allow_redirects=True,
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "")
            print(f"Content-Type: {content_type}")

            if "video" not in content_type and "octet-stream" not in content_type:
                print(f"⚠️  Warning: Unexpected content type: {content_type}")

            # Get file size
            content_length = response.headers.get("content-length")
            if content_length:
                file_size_mb = int(content_length) / (1024 * 1024)
                print(f"Expected file size: {file_size_mb:.2f} MB")
            else:
                print("File size: Unknown")

            filepath = os.path.join(download_path, filename)

            # Download with progress
            print("Downloading video...")
            total_downloaded = 0
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_downloaded += len(chunk)
                        if content_length:
                            progress = (total_downloaded / int(content_length)) * 100
                            print(f"\rProgress: {progress:.1f}%", end="", flush=True)
                        else:
                            print(
                                f"\rDownloaded: {total_downloaded / (1024 * 1024):.2f} MB",
                                end="",
                                flush=True,
                            )

            print()  # New line

            # Verify download
            if os.path.exists(filepath):
                actual_size = os.path.getsize(filepath)
                if actual_size > 0:
                    print(f"✅ Video downloaded successfully!")
                    print(f"📁 Saved to: {filepath}")
                    print(f"📊 File size: {actual_size / (1024 * 1024):.2f} MB")

                    end_time = time.time()
                    total_time = end_time - start_time
                    print(f"⏱️ Total time: {total_time:.2f} seconds")

                    return filepath
                else:
                    print("❌ Downloaded file is empty (0 bytes)")
                    os.remove(filepath)
                    return None
            else:
                print("❌ File was not created")
                return None

        except TimeoutException as e:
            print(f"❌ Timeout error: {e}")
            print(
                "The video processing took too long. The video might be too large or the server is busy."
            )
            return None
        except requests.RequestException as e:
            print(f"❌ Download error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def close(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
