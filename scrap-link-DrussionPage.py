from DrissionPage import ChromiumPage, ChromiumOptions
import json
import os

folder_path = r'E:\VSCODE\scrap-link\data'
file_name = "chapters_url_list.txt"

novel_url = "https://novelbin.com/b/primordial-villain-with-a-slave-harem#tab-chapters-title"


# 1. Create an options object
co = ChromiumOptions()

# 2. Set your browser path (Paste your path here)
# Use 'r' before the string to handle backslashes correctly
co.set_browser_path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')

# 3. Initialize the page with these options
page = ChromiumPage(addr_or_opts=co)

# Now your script should work
page.listen.start('ajax/chapter-archive')
page.get(novel_url)

print("Waiting for data...")
res = page.listen.wait()

data = res.response.body
print("\n--- Success! Data Captured ---")



#if url have special name for example novelbin create folder first
if "novelbin" in novel_url:
    folder_path = os.path.join(folder_path, "novelbin")
    novel_name = novel_url.replace("https://novelbin.com/b/", "").replace("#tab-chapters-title", "")
    folder_path = os.path.join(folder_path, novel_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    
    file_name = novel_name + "_chapters_url_list.txt"
    with open(os.path.join(folder_path, file_name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to {file_name} in folder {folder_path}")

    
page.quit()