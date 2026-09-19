"""
Central config for the Professional news bot.
Edit BANKS to add/remove firms. Everything else derives from this list.
"""

BANKS = [
    "Lazard", "Morgan Stanley", "Jefferies", "Bank of America", "BNP Paribas",
    "Wells Fargo", "Moelis", "JPMorgan", "Goldman Sachs", "Barclays",
    "Citigroup", "PJT Partners", "Evercore", "RBC Capital Markets",
    "Evolve Capital Partners",
]

GENERAL_MA_FEEDS = [
    "https://www.prnewswire.com/rss/financial-services-latest-news/mergers-acquisitions-list.rss",
    "https://www.businesswire.com/portal/site/home/news/subject/?vnsId=31382",
    "https://www.themiddlemarket.com/feed",
]

GOOGLE_NEWS_RSS_TEMPLATE = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)

def bank_query(bank: str) -> str:
    import urllib.parse
    q = f'"{bank}" ("advises" OR "advisor" OR "M&A" OR "acquisition" OR "merger")'
    return urllib.parse.quote(q)

def bank_feed_url(bank: str) -> str:
    return GOOGLE_NEWS_RSS_TEMPLATE.format(query=bank_query(bank))

import os
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY", "")
PUSHOVER_MA_TOKEN = os.environ.get("PUSHOVER_MA_TOKEN", "")
PUSHOVER_INDUSTRIALS_TOKEN = os.environ.get("PUSHOVER_INDUSTRIALS_TOKEN", "")
PUSHOVER_ALERTS_TOKEN = os.environ.get("PUSHOVER_ALERTS_TOKEN", "")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

STATE_FILE = "state/seen_articles.json"

MAX_ARTICLE_AGE_DAYS = 365  # 1 year

DAILY_LOG_FILE = "state/daily_log.json"  # every alert pushed today, reset after each morning brief
