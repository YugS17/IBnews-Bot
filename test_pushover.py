"""
Standalone Pushover connectivity test - completely independent of the RSS/AI
pipeline. Sends one test notification to each channel. If both arrive on your
phone, Pushover is correctly wired up and any remaining issue is elsewhere
(feeds, scoring, etc). If neither/one arrives, the problem is isolated to
the Pushover secrets or app tokens.
"""
import os
import sys
import requests

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

user_key = os.environ.get("PUSHOVER_USER_KEY", "")
ma_token = os.environ.get("PUSHOVER_MA_TOKEN", "")
industrials_token = os.environ.get("PUSHOVER_INDUSTRIALS_TOKEN", "")

missing = [name for name, val in [
    ("PUSHOVER_USER_KEY", user_key),
    ("PUSHOVER_MA_TOKEN", ma_token),
    ("PUSHOVER_INDUSTRIALS_TOKEN", industrials_token),
] if not val]

if missing:
    print(f"[FAIL] These secrets are empty or missing: {', '.join(missing)}")
    print("Check GitHub repo Settings > Secrets and variables > Actions - "
          "confirm each name matches EXACTLY and has a value.")
    sys.exit(1)

print(f"User key present: {len(user_key)} chars")
print(f"MA token present: {len(ma_token)} chars")
print(f"Industrials token present: {len(industrials_token)} chars")


def send_test(token: str, label: str):
    resp = requests.post(PUSHOVER_URL, data={
        "token": token,
        "user": user_key,
        "title": f"Test: {label}",
        "message": f"If you see this, your {label} channel is wired up correctly.",
        "priority": 0,
    }, timeout=15)

    print(f"\n[{label}] HTTP status: {resp.status_code}")
    print(f"[{label}] Response body: {resp.text}")

    if resp.status_code == 200:
        print(f"[{label}] Pushover ACCEPTED the request - check your phone now.")
    else:
        print(f"[{label}] Pushover REJECTED the request - see response body above "
              f"for the specific error (e.g. invalid token, invalid user key).")


send_test(ma_token, "M&A")
send_test(industrials_token, "Industrials")
