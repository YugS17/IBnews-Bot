"""
Standalone APITube API test. Verifies, with real calls:
1. That authentication works
2. What the rate-limit headers actually say (docs were inconsistent:
   100/day vs 30/30min)
3. Whether the 'title' param supports boolean OR grouping, by comparing a
   single-bank query against a multi-bank OR query
4. What a real response looks like, so we can build the real parser correctly

Run this manually once via test-apitube.yml before touching the main pipeline.
"""
import os
import sys
import requests

API_KEY = os.environ.get("APITUBE_API_KEY", "")
BASE_URL = "https://api.apitube.io/v1/news/everything"

if not API_KEY:
    print("[FAIL] APITUBE_API_KEY not set.")
    sys.exit(1)

HEADERS = {"X-API-Key": API_KEY}


def call(label, params):
    print(f"\n--- {label} ---")
    print(f"Params: {params}")
    resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=20)
    print(f"HTTP status: {resp.status_code}")

    rate_headers = {k: v for k, v in resp.headers.items() if "rate" in k.lower() or "limit" in k.lower()}
    if rate_headers:
        print(f"Rate limit headers: {rate_headers}")
    else:
        print("No rate-limit headers found in response.")

    if resp.status_code != 200:
        print(f"Response body: {resp.text[:500]}")
        return None

    data = resp.json()
    results = data.get("results", [])
    print(f"Total results returned: {len(results)}")
    if results:
        first = results[0]
        print(f"Sample article fields: {list(first.keys())}")
        print(f"Sample title: {first.get('title')}")
        print(f"Sample published_at: {first.get('published_at')}")
        print(f"Sample href: {first.get('href')}")
    return results


single_results = call("Single bank: Morgan Stanley, last 3 days", {
    "title": "Morgan Stanley",
    "published_at.start": "2026-09-17",
    "per_page": 10,
})

or_results = call("OR-grouped: multiple banks, last 3 days", {
    "title": "Morgan Stanley OR Goldman Sachs OR Evercore",
    "published_at.start": "2026-09-17",
    "per_page": 10,
})

comma_results = call("Comma-separated: multiple banks, last 3 days", {
    "title": "Morgan Stanley,Goldman Sachs,Evercore",
    "published_at.start": "2026-09-17",
    "per_page": 10,
})

print("\n=== SUMMARY ===")
print(f"Single-bank query: {len(single_results) if single_results is not None else 'FAILED'} results")
print(f"'OR' word query: {len(or_results) if or_results is not None else 'FAILED'} results")
print(f"Comma-separated query: {len(comma_results) if comma_results is not None else 'FAILED'} results")
print("\nIf the OR or comma query returned articles for MULTIPLE different "
      "banks (check titles above), that syntax works for real OR grouping. "
      "If it only matched articles containing the literal words 'OR' or a "
      "comma, we need a different approach (e.g. one request per bank).")
