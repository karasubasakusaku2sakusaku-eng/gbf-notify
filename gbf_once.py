import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

INDEX_URL = "https://granbluefantasy.jp/news/index.php"
STATE_FILE = "last_seen.txt"

def load_last_seen():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_seen(value: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(value)

def post(msg: str):
    r = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=25)
    r.raise_for_status()

def fetch_latest_from_site():
    headers = {"User-Agent": "Mozilla/5.0 (gbf-notify; GitHubActions)"}
    r = requests.get(INDEX_URL, headers=headers, timeout=25)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # ニュース一覧の一番上（最新）の記事リンクを取得
    for a in soup.select("h1 a"):
        href = a.get("href", "").strip()
        title = a.get_text(strip=True)
        if href and "pages/?p=" in href and title:
            url = href if href.startswith("http") else "https://granbluefantasy.jp" + href
            return title, url

    return None

def main():
    last = load_last_seen()
    latest = fetch_latest_from_site()
    if not latest:
        print("No latest article found")
        return

    title, url = latest

    # すでに送った記事なら何もしない
    if url == last:
        print("No new post")
        return

    post(f"📰 **グラブル公式サイト更新**\n{title}\n{url}")
    save_last_seen(url)
    print("Posted:", title)

if __name__ == "__main__":
    main()
