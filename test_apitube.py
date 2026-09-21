"""
Standalone APITube API test. Verifies, with real calls:
1. That authentication works
2. What the rate-limit headers actually say
3. Whether the 'title' param supports boolean OR grouping
4. Whether a proper industry/category taxonomy exists for more reliable filtering
5. What a real response looks like
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

    if resp.status_code != 200:
        print(f"Response body: {resp.text[:500]}")
        return None

    data = resp.json()
    results = data.get("results", [])
    print(f"Total results returned: {len(results)}")
    if results:
        first = results[0]
        print(f"Sample title: {first.get('title')}")
        print(f"Sample published_at: {first.get('published_at')}")
        if "industries" in first:
            print(f"Sample industries field: {first.get('industries')}")
        if "categories" in first:
            print(f"Sample categories field: {first.get('categories')}")
        if "entities" in first:
            print(f"Sample entities field: {first.get('entities')}")
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

print("\n\n########## ROUND 2 ##########")

multiword_results = call("Multi-word non-phrase: acquisition merger", {
    "title": "acquisition merger",
    "published_at.start": "2026-09-17",
    "per_page": 5,
})

industrials_category_results = call("Category filter attempt: industrials", {
    "category.name": "industrials",
    "published_at.start": "2026-09-17",
    "per_page": 5,
})

aerospace_industry_results = call("Industry filter attempt: aerospace", {
    "industry.name": "aerospace",
    "published_at.start": "2026-09-17",
    "per_page": 5,
})

entity_results = call("Entity filter attempt: Morgan Stanley as entity", {
    "entity.name": "Morgan Stanley",
    "published_at.start": "2026-09-17",
    "per_page": 5,
})

print("\n=== ROUND 2 SUMMARY ===")
print("Check above whether category.name / industry.name / entity.name "
      "returned 200 with real results, or errored/returned 0. If any of "
      "these work, we should use taxonomy filtering instead of pure text "
      "search for the Industrials channel - much more reliable.")
