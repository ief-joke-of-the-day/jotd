#!/usr/bin/env python3
"""Fetch today's joke deterministically from the calendar date and write joke.json.

Run daily by GitHub Actions. If the API fails, falls back to fallback_jokes.json
using the same date-based hash, so the page never breaks.
"""
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
SEARCH_URL = "https://icanhazdadjoke.com/search"
USER_AGENT = "joke-of-the-day (github.com/ief-joke-of-the-day/jotd)"


def date_seed(date_str: str) -> int:
    """Deterministic 32-bit FNV-1a hash of YYYY-MM-DD."""
    h = 0x811C9DC5
    for b in date_str.encode("ascii"):
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h


def fetch_for_date(date_str: str) -> str:
    seed = date_seed(date_str)
    # First query learns total_jokes so the index stays in range as the API grows.
    req = urllib.request.Request(
        f"{SEARCH_URL}?limit=1&page=1",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        meta = json.load(resp)
    total = int(meta["total_jokes"])
    if total <= 0:
        raise ValueError("no jokes returned")

    page = (seed % total) + 1
    if page == 1 and meta.get("results"):
        joke = meta["results"][0]["joke"].strip()
    else:
        req2 = urllib.request.Request(
            f"{SEARCH_URL}?limit=1&page={page}",
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            data = json.load(resp2)
        joke = data["results"][0]["joke"].strip()

    if not joke:
        raise ValueError("empty joke")
    return joke


def fallback(date_str: str) -> str:
    jokes = json.loads((HERE / "fallback_jokes.json").read_text(encoding="utf-8"))
    return jokes[date_seed(date_str) % len(jokes)]


def main() -> None:
    now = datetime.now(ZoneInfo("Europe/Zurich"))
    today = now.date().isoformat()
    out = HERE / "joke.json"

    if out.exists():
        try:
            if json.loads(out.read_text(encoding="utf-8")).get("date") == today:
                print("Joke for today already present.")
                return
        except json.JSONDecodeError:
            pass

    try:
        joke, source = fetch_for_date(today), "icanhazdadjoke.com"
    except Exception as exc:
        print(f"API failed ({exc}); using fallback.")
        joke, source = fallback(today), "fallback"

    out.write_text(
        json.dumps({"date": today, "joke": joke, "source": source}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"{today}: {joke}")


if __name__ == "__main__":
    main()
