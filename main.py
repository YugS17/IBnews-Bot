"""
Entry point. Run this on a schedule (see .github/workflows/news-bot.yml).
Fetch -> score -> push. Nothing is pushed unless the AI scorer confirms
a real match, so this stays high-precision rather than a keyword firehose.
"""
from fetch_feeds import fetch_new_articles
from score_relevance import score_articles
from notify import notify_ma_deal, notify_industrials


def main():
    new_articles, is_first_run = fetch_new_articles()
    print(f"Fetched {len(new_articles)} new candidate articles.")

    if not new_articles:
        return

    if is_first_run:
        print(f"First run detected - recorded {len(new_articles)} existing articles "
              f"as baseline without scoring/pushing them. Future runs will only "
              f"alert on articles published after this point.")
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
