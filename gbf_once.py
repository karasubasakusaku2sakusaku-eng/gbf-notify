import os
import requests
import xml.etree.ElementTree as ET

WEBHOOK_URL = os.environ["WEBHOOK_URL"]
RSS_URL = "https://nitter.net/granbluefantasy/rss"
STATE_FILE = "last_seen.txt"

def load_last_seen():
    try:
        return open(STATE_FILE).read().strip()
    except:
        return ""

def save_last_seen(v):
    open(STATE_FILE,"w").write(v)

def fetch_latest():
    r = requests.get(RSS_URL)
    root = ET.fromstring(r.text)
    item = root.find("./channel/item")
    return item.find("title").text, item.find("link").text

def post(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

last = load_last_seen()
title, link = fetch_latest()
if link != last:
    post(f"📢 グラブル公式\n{title}\n{link}")
    save_last_seen(link)
