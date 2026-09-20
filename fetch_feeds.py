"""
Pulls every configured feed and returns a flat list of new articles that
haven't been seen before. Feeds are fetched in parallel. Near-duplicate
stories from different publishers are collapsed into one candidate, so a
single real event doesn't trigger a burst of near-identical notifications.
Only articles actually selected for THIS run get marked as seen - overflow
carries over to future runs.
"""
import json
import os
import re
import hashlib
import calendar
from datetime import datetime, timezone
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser
import requests

from config import (
    BANKS, GENERAL_MA_FEEDS, INDUSTRIALS_FEEDS, bank_feed_url, STATE_FILE,
    MAX_ARTICLE_AGE_DAYS, MAX_ARTICLES_PER_RUN,
)

FEED_TIMEOUT_SECONDS = 10
MAX_WORKERS = 10
FUZZY_DUP_THRESHOLD = 0.6


def _entry_age_days(entry):
    struct_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not struct_time:
        return None
    published_dt = datetime.fromtimestamp(calendar.timegm(struct_time), tz=timezone.utc)
    age = datetime.now(timezone.utc) - published_dt
    return age.total_seconds() / 86400


def _article_id(entry) -> str:
    title = entry.get("title", "")
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
    normalized = re.sub(r"[^a-z0-9]+", "", title.lower())
    key = normalized or entry.get("link", "")
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _normalize_for_similarity(title: str) -> str:
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
    return re.sub(r"[^a-z0-9 ]+", "", title.lower()).strip()


def _dedupe_near_duplicates(candidates: list) -> list:
    """Collapses the same real-world story reported by different publishers
    with slightly different headlines into a single candidate."""
    representatives = []
    norm_titles = []
    for c in candidates:
        norm = _normalize_for_similarity(c["title"])
        matched_idx = None
        for idx, existing_norm in enumerate(norm_titles):
            if SequenceMatcher(None, norm, existing_norm).ratio() >= FUZZY_DUP_THRESHOLD:
                matched_idx = idx
                break
        if matched_idx is None:
            representatives.append(c)
            norm_titles.append(norm)
        else:
            if len(c.get("summary", "")) > len(representatives[matched_idx].get("summary", "")):
                representatives[matched_idx] = c
    return representatives


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
    seen = _load_seen()
    is_first_run = len(seen) == 0
    candidates = []

    all_feed_urls = list(GENERAL_MA_FEEDS) + list(INDUSTRIALS_FEEDS)
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

                age_days = _entry_age_days(entry)
                if age_days is not None and age_days > MAX_ARTICLE_AGE_DAYS:
                    seen.add(aid)
                    continue

                candidates.append({
                    "id": aid,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "source": parsed.feed.get("title", future_to_url[future]),
                    "age_days": age_days if age_days is not None else 0,
                })

    print(f"Done fetching. {len(candidates)} candidates within age window.")

    deduped = {}
    for c in candidates:
        deduped.setdefault(c["id"], c)
    candidates = list(deduped.values())

    before_fuzzy = len(candidates)
    candidates = _dedupe_near_duplicates(candidates)
    if before_fuzzy != len(candidates):
        print(f"Collapsed {before_fuzzy - len(candidates)} near-duplicate "
              f"stories from different publishers into single candidates.")

    if is_first_run:
        for c in candidates:
            seen.add(c["id"])
        _save_seen(seen)
        return candidates, is_first_run

    candidates.sort(key=lambda c: c["age_days"])
    selected = candidates[:MAX_ARTICLES_PER_RUN]
    overflow = len(candidates) - len(selected)

    for c in selected:
        seen.add(c["id"])
    _save_seen(seen)

    if overflow > 0:
        print(f"{overflow} additional candidates deferred to future runs "
              f"(per-run cap is {MAX_ARTICLES_PER_RUN}, newest prioritized).")

    return selected, is_first_run
