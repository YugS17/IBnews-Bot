"""
Sends an instant Pushover push notification. Every real alert also gets
appended to a daily log file, which daily_brief.py reads each morning to
build a summary, then clears.
"""
import json
import os
import requests

from config import (
    PUSHOVER_USER_KEY, PUSHOVER_MA_TOKEN, PUSHOVER_INDUSTRIALS_TOKEN,
    PUSHOVER_ALERTS_TOKEN, DAILY_LOG_FILE,
)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def _send(token: str, title: str, message: str, url: str = None, priority: int = 0):
    data = {
        "token": token,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "priority": priority,
    }
    if url:
        data["url"] = url
        data["url_title"] = "Read article"
    requests.post(PUSHOVER_URL, data=data, timeout=15)


def _log_for_daily_brief(channel: str, article: dict):
    try:
        os.makedirs(os.path.dirname(DAILY_LOG_FILE), exist_ok=True)
        entries = []
        if os.path.exists(DAILY_LOG_FILE):
            with open(DAILY_LOG_FILE, "r") as f:
                entries = json.load(f)
        entries.append({
            "channel": channel,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "reason": article.get("reason", ""),
            "link": article.get("link", ""),
        })
        with open(DAILY_LOG_FILE, "w") as f:
            json.dump(entries, f)
    except Exception as e:
        print(f"[warn] failed to log article for daily brief: {e}")


def notify_ma_deal(article: dict):
    _send(
        PUSHOVER_MA_TOKEN,
        title=f"M&A: {article['source']}",
        message=f"{article['title']}\n\n{article.get('reason', '')}",
        url=article["link"],
    )
    _log_for_daily_brief("ma", article)


def notify_industrials(article: dict):
    _send(
        PUSHOVER_INDUSTRIALS_TOKEN,
        title=f"Industrials Deal: {article['source']}",
        message=f"{article['title']}\n\n{article.get('reason', '')}",
        url=article["link"],
    )
    _log_for_daily_brief("industrials", article)


def notify_system_alert(error_summary: str):
    if not PUSHOVER_ALERTS_TOKEN:
        return
    try:
        _send(
            PUSHOVER_ALERTS_TOKEN,
            title="News Bot: workflow failed",
            message=error_summary[:1000],
            priority=1,
        )
    except Exception:
        pass


def notify_daily_brief(token: str, title: str, message: str):
    _send(token, title=title, message=message[:1000])
