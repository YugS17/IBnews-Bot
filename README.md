# Professional News Bot

Pushes an instant Pushover notification only when a real M&A deal involving one of
your tracked banks/advisories is announced — split into two channels:
- **M&A** (any sector)
- **Industrials** (subset of the above, industrials-sector deals only)

## One-time setup
1. Pushover ($5 one-time): sign up at pushover.net, install the app, copy your User Key,
   and create two Applications ("News M&A" and "News Industrials") for their tokens.
2. Anthropic API key from console.anthropic.com (pay-as-you-go).
3. Add four repo secrets: ANTHROPIC_API_KEY, PUSHOVER_USER_KEY, PUSHOVER_MA_TOKEN,
   PUSHOVER_INDUSTRIALS_TOKEN (Settings → Secrets and variables → Actions).
4. Enable Actions and run the "news-bot" workflow manually once to test.

## Tuning
- Add/remove banks: edit BANKS in config.py
- Change polling frequency: edit the cron line in the workflow file
- Adjust matching logic: edit SYSTEM_PROMPT in score_relevance.py
