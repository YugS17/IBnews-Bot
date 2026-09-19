"""
Entry point. Run this on a schedule (see .github/workflows/news-bot.yml).
Any unhandled failure anywhere in this pipeline triggers a separate
high-priority "system alert" push so a broken run surfaces immediately.
"""
import traceback
from fetch_feeds import fetch_new_articles
from score_relevance import score_articles
from notify import notify_ma_deal, notify_industrials, notify_system_alert


def run():
    new_articles, is_first_run = fetch_new_articles()
    print(f"Fetched {len(new_articles)} new candidate articles.")

    if not new_articles:
        return

    if is_first_run:
        print(f"First run detected - recorded {len(new_articles)} existing articles "
              f"as baseline without scoring/pushing them.")
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


def main():
    try:
        run()
    except Exception as e:
        error_summary = f"{type(e).__name__}: {e}"
        print(f"[FATAL] {error_summary}")
        traceback.print_exc()
        notify_system_alert(
            f"The news bot workflow failed with an error:\n\n{error_summary}\n\n"
            f"Check the GitHub Actions logs for the full traceback."
        )
        raise


if __name__ == "__main__":
    main()
