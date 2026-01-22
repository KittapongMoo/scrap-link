import os
import json
import time
import cloudscraper
import random
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "desktop": True
    }
)

# ---------------- CONFIG ----------------
NOVELS_DIR = "data/novelbin"
CONTENTS_DIR = "data/novel_contents"
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

def scrape_chapter_playwright(url, retries=3):
    for attempt in range(retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    slow_mo=500  # slows actions (looks human)
                )

                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )

                page = context.new_page()

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_load_state("networkidle", timeout=60000)
                    page.wait_for_selector("#chr-content", timeout=60000)

                    paragraphs = page.locator("#chr-content p").all_inner_texts()

                    if not paragraphs:
                        raise Exception("Chapter content empty")

                    return "\n\n".join(paragraphs)

                finally:
                    browser.close()

        except (PlaywrightTimeout, Exception) as e:
            if attempt < retries - 1:
                print(f"⚠️ Retry {attempt + 1}/{retries} for {url}")
                time.sleep(random.uniform(3, 7))
            else:
                raise Exception(f"Failed after {retries} retries: {e}")


def save_chapter(folder, url, content):
    title = url.split('/')[-1]  # Extract the title from the URL
    # Extract chapter number from 'chapter-X' pattern in the URL
    url_parts = url.split('/')
    chapter_part = [p for p in url_parts if p.startswith('chapter-')][0]
    chapter_no = int(chapter_part.replace('chapter-', '').split('-')[0])
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
    
def check_chapter_no(novel_folder):
    files = os.listdir(novel_folder)
    chapter_files = [f for f in files if f.endswith('.txt')]
    return len(chapter_files)
    
def main():
    novel_files = get_novel_files()
    #check contents
    print(novel_files)
    print(f"📚 Found {len(novel_files)} novels\n")

    for novel_file in novel_files:
        novel_path = os.path.join(NOVELS_DIR, novel_file)
        print(f"🔍 Processing novel file: {novel_path}")
        novel_url = load_novel(novel_path)
        
        novel_name = novel_file
        novel_folder = create_novel_folder(novel_name)
        
        contents_folder = os.path.join(CONTENTS_DIR, novel_name)
        cur_chapter_no = check_chapter_no(contents_folder) if os.path.exists(contents_folder) else 1
        print(f"Current chapter number starts from: {cur_chapter_no}")
        num_chapters = input("How many chapters do you want to scrape? (default: all): ").strip()
        num_chapters = int(num_chapters) if num_chapters.isdigit() else len(novel_url)
        
        for ch in novel_url[cur_chapter_no:cur_chapter_no+num_chapters]:
            try:
                title = ch.split('/')[-1]
                # Extract chapter number from 'chapter-X' pattern in the URL
                url_parts = ch.split('/')
                chapter_part = [p for p in url_parts if p.startswith('chapter-')][0]
                chapter_no = int(chapter_part.replace('chapter-', '').split('-')[0])
                filename = f"{chapter_no:04d} - {sanitize_filename(title)}.txt"
                
                if os.path.exists(os.path.join(novel_folder, filename)):
                    print(f"⏩ Skipped: {filename}")
                    continue
                
                # print("url:" + ch)
                content = scrape_chapter_playwright(ch)
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
