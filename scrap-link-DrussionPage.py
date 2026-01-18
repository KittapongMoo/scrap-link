from DrissionPage import ChromiumPage, ChromiumOptions
from urllib.parse import urlparse
import json
import os
import extract_url

BASE_FOLDER = r'E:\VSCODE\scrap-link\data'

# read URLs correctly
with open("url.txt", "r", encoding="utf-8") as f:
    novel_urls = [line.strip() for line in f if line.strip()]

# browser setup
co = ChromiumOptions()
co.set_browser_path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
page = ChromiumPage(addr_or_opts=co)

for novel_url in novel_urls:
    print(f"\n📖 Opening: {novel_url}")

    page.listen.start('ajax/chapter-archive')
    page.get(novel_url)

    print("⏳ Waiting for AJAX data...")
    res = page.listen.wait(timeout=10)

    if not res:
        print("❌ No AJAX data captured")
        continue

    data = res.response.body
    print("✅ Data captured")

    # handle NovelBin
    if "novelbin.com" in novel_url:
        parsed = urlparse(novel_url)
        novel_name = parsed.path.split("/b/")[1]

        novel_folder = os.path.join(BASE_FOLDER, "novelbin", novel_name)
        os.makedirs(novel_folder, exist_ok=True)

        file_path = os.path.join(novel_folder, "chapters_url_list.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"💾 Saved to: {file_path}")

page.quit()

extract_url.run()