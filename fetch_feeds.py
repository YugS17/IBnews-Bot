"""
Pulls every configured feed and returns a flat list of new articles
(title, link, summary, source) that haven't been seen before.
Feeds are fetched in parallel to avoid the multi-minute wall-clock time
of fetching 18 feeds one at a time.
"""
import json
import os
import hashlib
import calendar
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser
import requests

from config import BANKS, GENERAL_MA_FEEDS, bank_feed_url, STATE_FILE, MAX_ARTICLE_AGE_DAYS

FEED_TIMEOUT_SECONDS = 10
MAX_WORKERS = 10


def _entry_age_days(entry):
    """Returns how many days old this entry is, or None if it has no usable date."""
    struct_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not struct_time:
        return None
    published_dt = datetime.fromtimestamp(calendar.timegm(struct_time), tz=timezone.utc)
    age = datetime.now(timezone.utc) - published_dt
    return age.total_seconds() / 86400


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


def _fetch_one_feed(url: str):
    """Runs in a worker thread. Returns parsed feed or None on any failure."""
    try:
        resp = requests.get(
            url,
            timeout=FEED_TIMEOUT_SECONDS,
            headers={"User-Agent": "Mozilla/5.0 (news-bot RSS reader)"},
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception as e:
        print(f"[warn] failed to fetch {url}: {e}")
        return None


def fetch_new_articles():
    """Returns (new_articles, is_first_run)."""
    seen = _load_seen()
    is_first_run = len(seen) == 0
    new_articles = []

    all_feed_urls = list(GENERAL_MA_FEEDS)
    for bank in BANKS:
        all_feed_urls.append(bank_feed_url(bank))

    print(f"Fetching {len(all_feed_urls)} feeds in parallel...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(_fetch_one_feed, url): url for url in all_feed_urls}
        for future in as_completed(future_to_url):
            parsed = future.result()
            if parsed is None:
                continue

            for entry in parsed.entries:
                aid = _article_id(entry)
                if aid in seen:
                    continue
                seen.add(aid)

                age_days = _entry_age_days(entry)
                if age_days is not None and age_days > MAX_ARTICLE_AGE_DAYS:
                    continue

                new_articles.append({
                    "id": aid,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "source": parsed.feed.get("title", future_to_url[future]),
                })

    _save_seen(seen)
    print(f"Done fetching. {len(new_articles)} new articles within age window.")
    return new_articles, is_first_run
