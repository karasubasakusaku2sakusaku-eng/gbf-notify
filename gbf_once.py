import os
import time
import requests
import xml.etree.ElementTree as ET

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# まずは nitter を試す（X API不要）
RSS_URLS = [
    "https://nitter.net/granbluefantasy/rss",
]

STATE_FILE = "last_seen.txt"

def load_last_seen() -> str:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_seen(value: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(value)

def fetch_latest():
    headers = {
        "User-Agent": "Mozilla/5.0 (gbf-notify; GitHubActions)"
    }

    last_err = None
    for url in RSS_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=25)
            # 200以外は弾く
            r.raise_for_status()

            text = (r.text or "").strip()
            # 取得失敗（空）なら次へ
            if not text:
                last_err = f"Empty response from {url}"
                continue

            # XMLじゃないもの（HTML等）が返ったら次へ
            if "<rss" not in text and "<feed" not in text:
                last_err = f"Non-RSS response from {url} (starts with: {text[:30]!r})"
                continue

            root = ET.fromstring(text)
            item = root.find("./channel/item")
            if item is None:
                last_err = f"No <item> found in RSS from {url}"
                continue

            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            return title, link

        except Exception as e:
            last_err = f"{url}: {type(e).__name__}: {e}"
            continue

    # ここまで全部ダメなら「今回は何もしない」で終了（失敗扱いにしない）
    print("RSS fetch failed; skip this run:", last_err)
    return None

def post(msg: str):
    res = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=25)
    res.raise_for_status()

def main():
    last = load_last_seen()
    latest = fetch_latest()
    if not latest:
        return

    title, link = latest
    if link and link != last:
        post(f"📢 **グラブル公式**\n{title}\n{link}")
        save_last_seen(link)
        print("Posted:", title)
    else:
        print("No new post.")

if __name__ == "__main__":
    main()
