#!/usr/bin/env python3
"""Fetch today's joke and write joke.json. Standard library only.

Run daily by GitHub Actions. If the API fails, falls back to a local list
(picked by day of year), so the page never breaks.
To change the joke source, edit fetch_from_api() only.
"""
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
API_URL = "https://icanhazdadjoke.com/"
USER_AGENT = "joke-of-the-day (github.com/ief-jotd/joke-of-the-day)"


def fetch_from_api() -> str:
    req = urllib.request.Request(
        API_URL, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    joke = data["joke"].strip()
    if not joke:
        raise ValueError("empty joke")
    return joke


def fallback(day_of_year: int) -> str:
    jokes = json.loads((HERE / "fallback_jokes.json").read_text(encoding="utf-8"))
    return jokes[day_of_year % len(jokes)]


def main() -> None:
    now = datetime.now(ZoneInfo("Europe/Zurich"))
    today = now.date().isoformat()
    out = HERE / "joke.json"

    # Keep today's joke if this already ran today (re-runs don't change it).
    if out.exists():
        try:
            if json.loads(out.read_text(encoding="utf-8")).get("date") == today:
                print("Joke for today already present.")
                return
        except json.JSONDecodeError:
            pass

    try:
        joke, source = fetch_from_api(), "icanhazdadjoke.com"
    except Exception as exc:  # network error, bad JSON, ...
        print(f"API failed ({exc}); using fallback.")
        joke, source = fallback(now.timetuple().tm_yday), "fallback"

    out.write_text(
        json.dumps({"date": today, "joke": joke, "source": source}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"{today}: {joke}")


if __name__ == "__main__":
    main()
