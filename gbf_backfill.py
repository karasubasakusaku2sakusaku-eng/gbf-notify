import os
import time
import requests
import xml.etree.ElementTree as ET

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# まずは nitter を試す（必要なら増やせる）
RSS_URLS = [
    "https://nitter.net/granbluefantasy/rss",
]

STATE_FILE = "last_seen.txt"
BACKFILL_COUNT = int(os.environ.get("BACKFILL_COUNT", "10"))

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
    res = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=25)
    res.raise_for_status()

def fetch_items():
    headers = {"User-Agent": "Mozilla/5.0 (gbf-notify; GitHubActions)"}
    last_err = None

    for url in RSS_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=25)
            r.raise_for_status()
            text = (r.text or "").strip()

            # 空 or RSSじゃない（HTML等）なら次へ
            if not text:
                last_err = f"Empty response from {url}"
                continue
            if "<rss" not in text and "<feed" not in text:
                last_err = f"Non-RSS response from {url} (starts with: {text[:30]!r})"
                continue

            root = ET.fromstring(text)
            items = root.findall("./channel/item")
            if not items:
                last_err = f"No <item> found in RSS from {url}"
                continue

            return items

        except Exception as e:
            last_err = f"{url}: {type(e).__name__}: {e}"
            continue

    print("RSS fetch failed; skip this run:", last_err)
    return None

def main():
    items = fetch_items()
    if not items:
        return

    last_seen = load_last_seen()

    # 新しい順 → 条件一致だけ抽出
    filtered = []
    for it in items:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not title or not link:
            continue
        if not any(k in title for k in KEYWORDS):
            continue
        filtered.append((title, link))

    if not filtered:
        print("No matching items")
        return

    # 上からN件（新しい順）→ 送る時は古い→新しい順
    subset = filtered[:BACKFILL_COUNT]
    subset.reverse()

    newest_link_posted = None

    for title, link in subset:
        # last_seenに到達したらそれより古いのは送らない
        if last_seen and link == last_seen:
            print("Reached last_seen; stop")
            break

        post(f"🧪 **テスト反映（過去ログ）**\n📢 **グラブル公式**\n{title}\n{link}")
        newest_link_posted = link
        time.sleep(1.2)  # 連投しすぎ防止

    if newest_link_posted:
        save_last_seen(newest_link_posted)
        print("Updated last_seen to:", newest_link_posted)
    else:
        print("Nothing posted")

if __name__ == "__main__":
    main()
