"""
Pulls every configured feed and returns a flat list of new articles
(title, link, summary, source) that haven't been seen before.
"""
import json
import os
import hashlib
import feedparser
import requests

from config import BANKS, GENERAL_MA_FEEDS, bank_feed_url, STATE_FILE

FEED_TIMEOUT_SECONDS = 15


def _article_id(entry) -> str:
    key = entry.get("link") or entry.get("title", "")
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _load_seen() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r") as f:
        return set(json.load(f))


def _save_seen(seen: set):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    trimmed = list(seen)[-5000:]
    with open(STATE_FILE, "w") as f:
        json.dump(trimmed, f)


def fetch_new_articles() -> list[dict]:
    seen = _load_seen()
    new_articles = []

    all_feed_urls = list(GENERAL_MA_FEEDS)
    for bank in BANKS:
        all_feed_urls.append(bank_feed_url(bank))

    for url in all_feed_urls:
        try:
            resp = requests.get(
                url,
                timeout=FEED_TIMEOUT_SECONDS,
                headers={"User-Agent": "Mozilla/5.0 (news-bot RSS reader)"},
            )
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[warn] failed to fetch {url}: {e}")
            continue

        for entry in parsed.entries:
            aid = _article_id(entry)
            if aid in seen:
                continue
            seen.add(aid)
            new_articles.append({
                "id": aid,
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "source": parsed.feed.get("title", url),
            })

    _save_seen(seen)
    return new_articles
