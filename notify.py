"""
Sends an instant Pushover push notification.
Each sub-channel uses its OWN Pushover Application token, so they show up
as separate notification streams on your phone even from one account.
"""
import requests

from config import PUSHOVER_USER_KEY, PUSHOVER_MA_TOKEN, PUSHOVER_INDUSTRIALS_TOKEN

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def _send(token: str, title: str, message: str, url: str):
    requests.post(PUSHOVER_URL, data={
        "token": token,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "url": url,
        "url_title": "Read article",
        "priority": 0,
    }, timeout=15)


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
