"""
brave_image_search.py - query the Brave Image Search API and print one line
per result, largest images first.

The MCP web-search tool returns pages, not images. This script calls the
/images/search endpoint directly, which returns for every hit the FULL-SIZE
image URL, the page it sits on, the caption/title and the pixel size. Those
last two are free identification and resolution filters: read them before
downloading anything.

Usage:
    python brave_image_search.py "<query>" [count]
    python brave_image_search.py "<query>" --count 40 --safesearch strict

Requirements:
    Environment variable BRAVE_API_KEY must be set (the same key the
    brave-search MCP server and brave_llm_context.py use). The key is sent
    in a request header only; it is never printed.

Output lines (pipe separated, ASCII-safe, largest pixel area first):
    <width>x<height> | <full image url> | <source page url> | <title/caption>
Width/height are 0x0 when Brave does not report them - treat as unknown, not
small. A final line "RESULTS <n>" confirms the call ran, so an empty result
is distinguishable from a failed call (failures print "FAIL ..." and exit 1).

RESULTS 0 happens for valid queries. It means REPHRASE the query (different
wording, add or drop the year, name the event), never "no images exist".

Every URL is still just a lead: sidebar images of other people or items get
attached to the right page, and CDNs serve AVIF/WEBP under a .jpg name. Open
each candidate before keeping it.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://api.search.brave.com/res/v1/images/search"
MAX_COUNT = 200


def ascii_safe(text):
    """Make text printable on any console (cp1252 included)."""
    return text.encode("ascii", "replace").decode("ascii")


def scrub(text, key):
    """Never let the API key reach the output, whatever the error text holds."""
    return text.replace(key, "***") if key else text


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Brave image search: full-size URL, WxH, source page and "
        "caption per result, largest first."
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "count_pos",
        nargs="?",
        type=int,
        metavar="count",
        help="Number of results (1-%d, default 40)" % MAX_COUNT,
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Same as the positional count (1-%d, default 40)" % MAX_COUNT,
    )
    parser.add_argument(
        "--safesearch",
        choices=["off", "strict"],
        default="strict",
        help="Brave safesearch level (default: strict)",
    )
    args = parser.parse_args()
    count = args.count if args.count is not None else args.count_pos
    if count is None:
        count = 40
    args.count = max(1, min(count, MAX_COUNT))
    return args


def main():
    args = parse_args()
    key = os.environ.get("BRAVE_API_KEY", "")
    if not key:
        print("FAIL no BRAVE_API_KEY in environment")
        sys.exit(1)

    params = urllib.parse.urlencode(
        {"q": args.query, "count": args.count, "safesearch": args.safesearch}
    )
    req = urllib.request.Request(
        ENDPOINT + "?" + params,
        headers={"Accept": "application/json", "X-Subscription-Token": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        print(ascii_safe(scrub("FAIL HTTP %s %s %s" % (exc.code, exc.reason, body), key)))
        sys.exit(1)
    except Exception as exc:
        print(ascii_safe(scrub("FAIL %s" % exc, key)))
        sys.exit(1)

    rows = []
    for item in data.get("results", []):
        props = item.get("properties") or {}
        width = to_int(props.get("width"))
        height = to_int(props.get("height"))
        img_url = props.get("url") or ""
        page_url = item.get("url") or ""
        # Brave's "title" is the caption; it often carries event and date.
        title = " ".join((item.get("title") or "").replace("|", "/").split())
        rows.append((width * height, width, height, img_url, page_url, title))
    rows.sort(key=lambda r: r[0], reverse=True)
    for _, width, height, img_url, page_url, title in rows:
        line = "%sx%s | %s | %s | %s" % (width, height, img_url, page_url, title)
        print(ascii_safe(line))
    print("RESULTS %d" % len(rows))
    if not rows:
        print("NOTE zero results: rephrase the query; this does not mean no images exist")


if __name__ == "__main__":
    main()
