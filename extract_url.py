import re
from urllib.parse import urlparse
import os

def run():
    BASE_FOLDER = r'E:\VSCODE\scrap-link\data'
    # read URLs correctly
    with open("url.txt", "r", encoding="utf-8") as f:
        novel_urls = [line.strip() for line in f if line.strip()]
        
    for novel_url in novel_urls:
        if "novelbin.com" in novel_url:
            parsed = urlparse(novel_url)
            novel_name = parsed.path.split("/b/")[1]

            novel_folder = os.path.join(BASE_FOLDER, "novelbin", novel_name)
            
            input_file = os.path.join(novel_folder, "chapters_url_list.json")
            output_file = os.path.join(novel_folder, "chapter_urls_clean.json")

            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()

            # extract all novelbin chapter URLs
            urls = re.findall(
                r'https://novelbin\.com/b/[^"]+',
                text
            )
        
        # 🔥 CLEAN URLs (remove trailing \, /, whitespace)
        clean_urls = []
        for u in urls:
            u = u.rstrip("\\/ \n\r\t")
            clean_urls.append(u)

        # remove duplicates while keeping order
        urls = list(dict.fromkeys(clean_urls))

        # save as proper formatted JSON
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(urls, f, indent=4, ensure_ascii=False)

        print(f"✅ Extracted {len(urls)} chapter URLs")
        print(f"💾 Saved to {output_file}")
