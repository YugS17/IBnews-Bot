"""
Scores each candidate article against your two Professional sub-channels
using an LLM call, so we only push genuine matches - not just keyword hits.
"""
import json
import requests

from config import ANTHROPIC_API_KEY, BANKS

SYSTEM_PROMPT = f"""You are a filter for a personal news alert bot. The user is an MBA
student targeting Industrials-coverage investment banking. He only wants to be pushed
a notification for articles that are genuinely relevant - not just loosely related.

He tracks these banks/advisories: {", ".join(BANKS)}.

For each article, decide:
1. "ma_deal": true if the article reports a specific, real M&A transaction (announced,
   completed, or rumored with credible sourcing) where one of the tracked banks/advisories
   is acting as financial advisor, on either side of the deal.
2. "bank_news": true if the article is about one of the tracked banks/advisories directly -
   specifically their EARNINGS RELEASES (quarterly/annual results, guidance) or HIRING/
   PERSONNEL news (senior banker hires, departures, promotions, team build-outs) - even if
   it's not a specific M&A transaction. General unrelated commentary, opinion pieces, or a
   bank merely being mentioned in passing should be false for both ma_deal and bank_news.
3. "industrials": true if, in addition to being a real M&A deal from a tracked bank
   (ma_deal is true), the deal itself is in the industrials sector (manufacturing,
   aerospace & defense, building products, machinery, diversified industrials, industrial
   distribution, chemicals-as-industrial-inputs, etc), OR if a bank_news item (hiring/
   earnings) specifically concerns their Industrials coverage group. If the deal/news is in
   an unrelated sector or group, industrials should be false.

Respond with ONLY a JSON array, one object per article, in the same order given, like:
[{{"ma_deal": true, "bank_news": false, "industrials": false, "reason": "one short sentence"}}, ...]
No markdown, no preamble."""


def score_articles(articles: list[dict]) -> list[dict]:
    """Returns the same articles, each annotated with ma_deal / bank_news / industrials / reason."""
    if not articles:
        return []

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set - cannot score articles.")

    scored = []
    batch_size = 15
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        user_content = "\n\n".join(
            f"[{j}] TITLE: {a['title']}\nSUMMARY: {a['summary'][:400]}"
            for j, a in enumerate(batch)
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
                "max_tokens": 2000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_content}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        results = json.loads(text)

        for a, r in zip(batch, results):
            a["ma_deal"] = r.get("ma_deal", False)
            a["bank_news"] = r.get("bank_news", False)
            a["industrials"] = r.get("industrials", False)
            a["reason"] = r.get("reason", "")
            scored.append(a)

    return scored
