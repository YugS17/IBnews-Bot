"""
Run once a day (see .github/workflows/daily-brief.yml). Reads everything
notify.py logged since the last brief, asks Claude to write a short summary
per channel, pushes that summary, then clears the log so tomorrow starts fresh.
"""
import json
import os
import sys
import requests

from config import (
    ANTHROPIC_API_KEY, PUSHOVER_MA_TOKEN, PUSHOVER_INDUSTRIALS_TOKEN,
    DAILY_LOG_FILE,
)
from notify import notify_daily_brief, notify_system_alert


def _load_and_clear_log() -> list[dict]:
    if not os.path.exists(DAILY_LOG_FILE):
        return []
    with open(DAILY_LOG_FILE, "r") as f:
        entries = json.load(f)
    with open(DAILY_LOG_FILE, "w") as f:
        json.dump([], f)
    return entries


def _summarize(channel_label: str, entries: list[dict]) -> str:
    if not entries:
        return f"No new {channel_label} alerts in the last 24 hours - quiet day."

    if not ANTHROPIC_API_KEY:
        return "\n".join(f"- {e['title']} ({e['source']})" for e in entries[:15])

    items_text = "\n".join(
        f"- {e['title']} ({e['source']}): {e.get('summary_text', '')}" for e in entries
    )
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 400,
            "system": (
                "You write a short morning briefing for an MBA student targeting "
                "Industrials-coverage investment banking. Given today's headlines "
                "for one channel, write a concise 3-5 sentence summary highlighting "
                "the most notable items and any patterns (e.g. multiple deals from "
                "the same bank). Plain text only, no markdown, no headers."
            ),
            "messages": [{"role": "user", "content": items_text}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()


def main():
    entries = _load_and_clear_log()
    ma_entries = [e for e in entries if e["channel"] == "ma"]
    industrials_entries = [e for e in entries if e["channel"] == "industrials"]

    ma_summary = _summarize("M&A", ma_entries)
    industrials_summary = _summarize("Industrials", industrials_entries)

    notify_daily_brief(
        PUSHOVER_MA_TOKEN,
        title=f"Morning Brief: M&A ({len(ma_entries)} today)",
        message=ma_summary,
    )
    notify_daily_brief(
        PUSHOVER_INDUSTRIALS_TOKEN,
        title=f"Morning Brief: Industrials ({len(industrials_entries)} today)",
        message=industrials_summary,
    )

    print(f"Sent daily brief - {len(ma_entries)} M&A items, "
          f"{len(industrials_entries)} Industrials items summarized.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {type(e).__name__}: {e}")
        notify_system_alert(f"Daily brief failed: {type(e).__name__}: {e}")
        sys.exit(1)
