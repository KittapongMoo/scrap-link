import os
import json
import time
import cloudscraper
import random
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

p = sync_playwright().start()

browser = p.chromium.launch(
    headless=False,
    slow_mo=100
)

context = browser.new_context(
    viewport={"width": 1280, "height": 800},
    user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
)

# Block heavy resources
context.route(
    "**/*",
    lambda route: route.abort()
    if route.request.resource_type in ["image", "font", "media"]
    else route.continue_()
)

scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "desktop": True
    }
)

# ---------------- CONFIG ----------------
NOVELS_DIR = "data/novelbin"
OUTPUT_DIR = "data/novel_contents"
DELAY = 1  # seconds between requests
# ----------------------------------------

scraper = cloudscraper.create_scraper()

def get_novel_files():
    return [f for f in os.listdir(NOVELS_DIR) if os.path.isdir(os.path.join(NOVELS_DIR, f))]

def load_novel(path):
    file_path = os.path.join(path, "chapter_urls_clean.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_novel_folder(novel_name):
    folder = os.path.join(OUTPUT_DIR, novel_name)
    os.makedirs(folder, exist_ok=True)
    print(f"📁 Created folder: {folder}")
    return folder

def sanitize_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|')

def scrape_chapter(url, retries=3):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://novelbin.com/"
    }

    for attempt in range(retries):
        try:
            response = scraper.get(
                url,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()

            if "cloudflare" in response.text.lower():
                raise Exception("Cloudflare block detected")

            soup = BeautifulSoup(response.text, "html.parser")

            content_div = soup.find("div", id="chr-content")
            if not content_div:
                raise Exception("Chapter content not found")

            paragraphs = content_div.find_all("p")
            return "\n\n".join(
                p.get_text(strip=True)
                for p in paragraphs
                if p.get_text(strip=True)
            )

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Retry {attempt + 1}/{retries} for {url}")
            time.sleep(random.uniform(3, 7))

    raise Exception("Failed after retries")

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def scrape_chapter_playwright(url):
    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#chr-content", timeout=30000)
    text = page.locator("#chr-content p").all_inner_texts()
    page.close()
    return "\n\n".join(text)


def save_chapter(folder, url, content):
    title = url.split('/')[-1]  # Extract the title from the URL
    chapter_no = int(url.split('-')[-1].split('/')[-1].replace('chapter-', ''))  # Extract the chapter number
    print("title :" + title)
    print("chapter_no :" + str(chapter_no))
    filename = f"{chapter_no:04d} - {sanitize_filename(title)}.txt"
    path = os.path.join(folder, filename)

    if os.path.exists(path):
        print(f"⏩ Skipped: {filename}")
        return

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Saved: {filename}")

def main():
    novel_files = get_novel_files()
    #check contents
    print(novel_files)
    print(f"📚 Found {len(novel_files)} novels\n")

    for novel_file in novel_files:
        novel_path = os.path.join(NOVELS_DIR, novel_file)
        print(f"🔍 Processing novel file: {novel_path}")
        novel_url = load_novel(novel_path)
        # print(novel_url)

        novel_name = novel_file
        novel_folder = create_novel_folder(novel_name)

        for ch in novel_url[:2]:
            try:
                print( "url:" + ch)
                # break
                content = scrape_chapter_playwright(ch)
                print("content:" + content[:100])
                # break
                save_chapter(
                    novel_folder,
                    ch,
                    content
                )
                time.sleep(DELAY)
            except Exception as e:
                print(f"❌ Chapter {ch} failed: {e}")

        print("-" * 50)

if __name__ == "__main__":
    main()
