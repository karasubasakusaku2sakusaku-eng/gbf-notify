import os
import requests
import xml.etree.ElementTree as ET

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# グラブル公式（X @granbluefantasy）
RSS_URLS = [
    "https://nitter.net/granbluefantasy/rss",
]

STATE_FILE = "last_seen.txt"

# === すぐる指定：拾いたいキーワード ===
KEYWORDS = [
    # ガチャ系
    "ガチャ", "レジェンドガチャ", "グランデフェス", "レジェフェス",

    # アップデート系
    "アップデート", "更新", "実装", "追加", "最終上限解放", "バランス調整",

    # 追加指定
    "スキン", "キャンペーン", "開催", "グラブルフェス",
    "紹介", "セット", "サプライズ",
]

def load_last_seen():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_seen(value):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(value)

def fetch_latest():
    headers = {"User-Agent": "Mozilla/5.0 (gbf-notify; GitHubActions)"}

    for url in RSS_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=25)
            r.raise_for_status()
            text = (r.text or "").strip()

            # RSSじゃないものはスキップ
            if not text or ("<rss" not in text and "<feed" not in text):
                continue

            root = ET.fromstring(text)
            item = root.find("./channel/item")
            if item is None:
                continue

            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            return title, link
        except Exception:
            continue

    return None

def post(msg):
    requests.post(WEBHOOK_URL, json={"content": msg}, timeout=25)

def main():
    last = load_last_seen()
    latest = fetch_latest()
    if not latest:
        print("RSS not available this run")
        return

    title, link = latest

    # キーワードフィルタ
    if not any(k in title for k in KEYWORDS):
        print("Filtered out:", title)
        return

    # すでに送った投稿なら何もしない
    if link == last:
        print("No new post")
        return

    post(f"📢 **グラブル公式**\n{title}\n{link}")
    save_last_seen(link)
    print("Posted:", title)

if __name__ == "__main__":
    main()
