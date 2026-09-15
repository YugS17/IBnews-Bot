"""
Entry point. Run this on a schedule (see .github/workflows/news-bot.yml).
"""
from fetch_feeds import fetch_new_articles
from score_relevance import score_articles
from notify import notify_ma_deal, notify_industrials


def main():
    new_articles = fetch_new_articles()
    print(f"Fetched {len(new_articles)} new candidate articles.")

    if not new_articles:
        return

    scored = score_articles(new_articles)

    ma_count = industrials_count = 0
    for article in scored:
        if article["industrials"]:
            notify_industrials(article)
            industrials_count += 1
        elif article["ma_deal"]:
            notify_ma_deal(article)
            ma_count += 1

    print(f"Pushed {ma_count} M&A alerts, {industrials_count} Industrials alerts. "
          f"Discarded {len(scored) - ma_count - industrials_count} near-misses.")


if __name__ == "__main__":
    main()
