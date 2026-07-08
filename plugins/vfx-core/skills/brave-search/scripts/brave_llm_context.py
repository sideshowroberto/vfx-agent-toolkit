"""
brave_llm_context.py
Direct caller for the Brave Search LLM Context API endpoint.

The MCP server only exposes /web/search and /local/search.
This script provides access to /llm/context - which returns actual extracted
page content rather than URLs + snippets. Use this for deep research tasks.

Usage:
    python brave_llm_context.py "your query here"
    python brave_llm_context.py "Houdini VEX wrangles tutorial" --tokens 16384
    python brave_llm_context.py "USD Solaris documentation" --freshness pm --threshold strict
    python brave_llm_context.py "query" --count 10 --urls 5 --tokens 8192

Requirements:
    pip install requests
    Environment variable: BRAVE_API_KEY must be set

Output:
    Prints extracted content to stdout, formatted for Claude to read directly.
    Each source is shown with its URL, title, and extracted text chunks.
"""

import argparse
import json
import os
import sys

# Windows consoles default to cp1252 - printing extracted web content with
# characters outside that codepage raises UnicodeEncodeError. Force UTF-8.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)


ENDPOINT = "https://api.search.brave.com/res/v1/llm/context"


def get_api_key():
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        print("ERROR: BRAVE_API_KEY environment variable not set.")
        print("Set it with: $env:BRAVE_API_KEY = 'your-key'  (PowerShell)")
        print("Or add it to your system environment variables.")
        sys.exit(1)
    return key


def llm_context(
    query,
    tokens=8192,
    count=20,
    urls=20,
    snippets=50,
    freshness=None,
    threshold="balanced",
    country="US",
    lang="en",
):
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": get_api_key(),
    }

    params = {
        "q": query,
        "maximum_number_of_tokens": tokens,
        "count": count,
        "maximum_number_of_urls": urls,
        "maximum_number_of_snippets": snippets,
        "context_threshold_mode": threshold,
        "country": country,
        "search_lang": lang,
    }

    if freshness:
        params["freshness"] = freshness

    try:
        response = requests.get(ENDPOINT, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 30 seconds.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP {response.status_code} - {response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def format_output(data, query):
    grounding = data.get("grounding", {})
    sources = data.get("sources", {})
    results = grounding.get("generic", [])

    if not results:
        print(f"No results found for: {query}")
        return

    print(f"=== Brave LLM Context: {query} ===")
    print(f"Sources: {len(results)} | Token budget used")
    print()

    for i, result in enumerate(results, 1):
        url = result.get("url", "")
        title = result.get("title", "")
        snippets = result.get("snippets", [])

        # Get source metadata
        source_meta = sources.get(url, {})
        hostname = source_meta.get("hostname", "")
        age = source_meta.get("age", [""])[0] if source_meta.get("age") else ""

        print(f"--- Source {i}: {title} ---")
        print(f"URL: {url}")
        if age:
            print(f"Age: {age}")
        print()

        for snippet in snippets:
            print(snippet)
            print()

    print(f"=== End of LLM Context ({len(results)} sources) ===")


def main():
    parser = argparse.ArgumentParser(
        description="Call Brave Search LLM Context API for deep research"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--tokens",
        type=int,
        default=8192,
        help="Max tokens in response (1024-32768, default 8192). Use 16384-32768 for deep research.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Search results to evaluate (1-50, default 20)",
    )
    parser.add_argument(
        "--urls",
        type=int,
        default=20,
        help="Max source URLs to extract from (1-50, default 20)",
    )
    parser.add_argument(
        "--snippets",
        type=int,
        default=50,
        help="Max text chunks total (1-100, default 50)",
    )
    parser.add_argument(
        "--freshness",
        choices=["pd", "pw", "pm", "py"],
        help="pd=24h, pw=7d, pm=31d, py=365d",
    )
    parser.add_argument(
        "--threshold",
        choices=["disabled", "strict", "balanced", "lenient"],
        default="balanced",
        help="Content quality threshold (default: balanced). Use strict for authoritative sources only.",
    )
    parser.add_argument("--country", default="US", help="Country code (default: US)")
    parser.add_argument("--lang", default="en", help="Language (default: en)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")

    args = parser.parse_args()

    data = llm_context(
        query=args.query,
        tokens=args.tokens,
        count=args.count,
        urls=args.urls,
        snippets=args.snippets,
        freshness=args.freshness,
        threshold=args.threshold,
        country=args.country,
        lang=args.lang,
    )

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        format_output(data, args.query)


if __name__ == "__main__":
    main()
