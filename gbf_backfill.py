import os
import time
import requests
import xml.etree.ElementTree as ET

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

RSS_URL = "https://nitter.net/granbluefantasy/rss"
STATE_FILE = "last_seen.txt"

# 何件流すか（デフォ10）
BACKFILL_COUNT = int(os.environ.get("BACKFILL_COUNT", "10"))

# === すぐる指定：拾いたいキーワード（本番と同じ） ===
KEYWORDS = [
    "ガチャ", "レジェンドガチャ", "グランデフェス", "レジェフェス",
    "アップデート", "更新", "実装", "追加", "最終上限解放", "バランス調整",
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

def post(msg):
    requests.post(WEBHOOK_URL, json={"content": msg}, timeout=25)

def main():
    headers = {"User-Agent": "Mozilla/5.0 (gbf-notify; GitHubActions)"}
    r = requests.get(RSS_URL, headers=headers, timeout=25)
    r.raise_for_status()
    text = (r.text or "").strip()
    root = ET.fromstring(text)

    items = root.findall("./channel/item")
    if not items:
        print("No items")
        return

    last_seen = load_last_seen()

    # RSSは新しい順で並ぶので、いったんキーワードで絞って、上からN件取り、古い→新しい順で送る
    filtered = []
    for it in items:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link or not title:
            continue
        if not any(k in title for k in KEYWORDS):
            continue
        filtered.append((title, link))

    if not filtered:
        print("No matching items")
        return

    subset = filtered[:BACKFILL_COUNT]
    subset.reverse()  # 古い→新しい順にする

    posted_any = False
    newest_link_posted = None

    for title, link in subset:
        # すでに last_seen と同じリンクなら、その投稿より前は送らない（無限再投下防止）
        if last_seen and link == last_seen:
            print("Reached last_seen; stop")
            break

        post(f"🧪 **テスト反映（過去ログ）**\n📢 **グラブル公式**\n{title}\n{link}")
        posted_any = True
        newest_link_posted = link
        time.sleep(1.2)  # 連投しすぎ防止

    # last_seen を最新に更新（次から通常Botが重複で流しにくいように）
    if posted_any and newest_link_posted:
        save_last_seen(newest_link_posted)
        print("Updated last_seen to:", newest_link_posted)
    else:
        print("Nothing posted")

if __name__ == "__main__":
    main()
