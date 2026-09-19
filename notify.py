"""
Sends an instant Pushover push notification.
Each sub-channel uses its OWN Pushover Application token, so they show up
as separate, clearly-labeled notification streams on your phone even
though it's one Pushover account.
"""
import requests

from config import (
    PUSHOVER_USER_KEY, PUSHOVER_MA_TOKEN, PUSHOVER_INDUSTRIALS_TOKEN,
    PUSHOVER_ALERTS_TOKEN,
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


def notify_ma_deal(article: dict):
    _send(
        PUSHOVER_MA_TOKEN,
        title=f"M&A: {article['source']}",
        message=f"{article['title']}\n\n{article.get('reason', '')}",
        url=article["link"],
    )


def notify_industrials(article: dict):
    _send(
        PUSHOVER_INDUSTRIALS_TOKEN,
        title=f"Industrials Deal: {article['source']}",
        message=f"{article['title']}\n\n{article.get('reason', '')}",
        url=article["link"],
    )


def notify_system_alert(error_summary: str):
    """Pushes a system/ops alert to a SEPARATE channel from news content,
    so a broken pipeline surfaces immediately."""
    if not PUSHOVER_ALERTS_TOKEN:
        return
    try:
        _send(
            PUSHOVER_ALERTS_TOKEN,
            title="News Bot: workflow failed",
            message=error_summary[:1000],
            priority=1,  # high priority - bypasses phone quiet hours
        )
    except Exception:
        pass
