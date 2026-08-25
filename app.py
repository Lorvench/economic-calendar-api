"""Economic Calendar API.

Fetches the Investing.com economic-calendar feed and exposes the parsed events as
JSON.  The payload intentionally mirrors the original PHP endpoint.
"""

from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from flask import Flask, Response, json


SOURCE_URL = "https://sslecal2.forexprostools.com/"
REQUEST_TIMEOUT_SECONDS = 30

app = Flask(__name__)


def sanitize(value: str) -> str:
    """Match PHP's trim(str_replace('&nbsp;', '', value)) behaviour."""
    return value.replace("\u00a0", "").replace("&nbsp;", "").strip()


def cell_text(row: Tag, selector: str) -> str | None:
    cell = row.select_one(selector)
    return sanitize(cell.get_text()) if cell is not None else None


def parse_events(html: str) -> list[dict[str, Any]]:
    """Extract the same fields and fallback values as the legacy PHP parser."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("#ecEventsTable")
    if table is None:
        return []

    events: list[dict[str, Any]] = []
    for row in table.select("tr[id*='eventRowId']"):
        sentiment = row.select_one("td.sentiment")
        events.append(
            {
                "economy": cell_text(row, "td.flagCur") or "",
                "impact": len(sentiment.select("i.grayFullBullishIcon")) if sentiment else 0,
                "data": row.get("event_timestamp"),
                "name": cell_text(row, "td.event"),
                "actual": cell_text(row, "td.act"),
                "forecast": cell_text(row, "td.fore"),
                "previous": cell_text(row, "td.prev"),
            }
        )
    return events


def fetch_calendar() -> list[dict[str, Any]]:
    response = requests.get(SOURCE_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return parse_events(response.text)


@app.get("/")
def calendar() -> Response:
    """Return the current economic calendar as a JSON array."""
    return Response(json.dumps(fetch_calendar()), mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
