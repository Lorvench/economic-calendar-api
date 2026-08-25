"""Resilient economic-calendar API for Flask and Render."""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests
from flask import Flask, Response, jsonify, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://api.tradingeconomics.com/calendar"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("CALENDAR_REQUEST_TIMEOUT_SECONDS", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CALENDAR_CACHE_TTL_SECONDS", "900"))
STALE_CACHE_TTL_SECONDS = int(os.getenv("CALENDAR_STALE_CACHE_TTL_SECONDS", "86400"))
FAILURE_BACKOFF_SECONDS = int(os.getenv("CALENDAR_FAILURE_BACKOFF_SECONDS", "60"))

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


class CalendarProviderError(Exception):
    """A safe, public-facing error from the calendar provider."""


@dataclass
class CacheEntry:
    data: list[dict[str, Any]]
    fetched_at: float


cache_lock = threading.Lock()
cache: CacheEntry | None = None
next_provider_attempt_at = 0.0


def build_http_session() -> requests.Session:
    """Retry transient upstream failures a small, bounded number of times."""
    retry = Retry(total=2, connect=2, read=2, status=2, backoff_factor=0.5,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(("GET",)), raise_on_status=False)
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


http = build_http_session()


def _string_or_none(value: Any) -> str | None:
    return None if value is None else str(value).strip()


def normalize_events(payload: Any) -> list[dict[str, Any]]:
    """Validate Trading Economics JSON and retain the legacy event field names."""
    if not isinstance(payload, list):
        raise CalendarProviderError("Calendar provider returned invalid data")

    events: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise CalendarProviderError("Calendar provider returned invalid data")
        name = _string_or_none(item.get("Event")) or _string_or_none(item.get("Category"))
        if name is None:
            raise CalendarProviderError("Calendar provider returned invalid data")
        try:
            impact = int(item.get("Importance", 0) or 0)
        except (TypeError, ValueError) as error:
            raise CalendarProviderError("Calendar provider returned invalid data") from error
        events.append({
            "economy": _string_or_none(item.get("Currency")) or _string_or_none(item.get("Country")) or "",
            "impact": impact,
            "data": _string_or_none(item.get("Date")),
            "name": name,
            "actual": _string_or_none(item.get("Actual")),
            "forecast": _string_or_none(item.get("Forecast")),
            "previous": _string_or_none(item.get("Previous")),
        })
    return events


def fetch_calendar() -> list[dict[str, Any]]:
    """Fetch and validate fresh data without leaking provider errors to clients."""
    api_key = os.getenv("TRADING_ECONOMICS_API_KEY")
    if not api_key:
        logger.error("Calendar provider is not configured: TRADING_ECONOMICS_API_KEY is missing")
        raise CalendarProviderError("Economic calendar provider temporarily unavailable")
    try:
        response = http.get(API_URL, params={"c": api_key, "f": "json"},
                            headers={"Accept": "application/json"}, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code in (403, 429) or response.status_code >= 500:
            logger.warning("Calendar provider returned HTTP %s", response.status_code)
        response.raise_for_status()
        return normalize_events(response.json())
    except requests.exceptions.Timeout as error:
        logger.warning("Calendar provider request timed out")
        raise CalendarProviderError("Economic calendar provider temporarily unavailable") from error
    except requests.exceptions.HTTPError as error:
        logger.warning("Calendar provider request failed with HTTP %s", error.response.status_code)
        raise CalendarProviderError("Economic calendar provider temporarily unavailable") from error
    except requests.exceptions.RequestException as error:
        logger.warning("Calendar provider request failed: %s", error.__class__.__name__)
        raise CalendarProviderError("Economic calendar provider temporarily unavailable") from error
    except (TypeError, ValueError, CalendarProviderError) as error:
        logger.warning("Calendar provider returned invalid data")
        raise CalendarProviderError("Economic calendar provider temporarily unavailable") from error


def calendar_data() -> tuple[list[dict[str, Any]] | None, str, bool]:
    """Return fresh data, cached data, or a safe provider-unavailable result."""
    global cache, next_provider_attempt_at
    now = time.monotonic()
    with cache_lock:
        if cache and now - cache.fetched_at < CACHE_TTL_SECONDS:
            return cache.data, "cache", False
        if now < next_provider_attempt_at:
            if cache and now - cache.fetched_at < STALE_CACHE_TTL_SECONDS:
                return cache.data, "stale_cache", True
            return None, "unavailable", False
    try:
        fresh_data = fetch_calendar()
    except CalendarProviderError:
        with cache_lock:
            next_provider_attempt_at = time.monotonic() + FAILURE_BACKOFF_SECONDS
            if cache and now - cache.fetched_at < STALE_CACHE_TTL_SECONDS:
                return cache.data, "stale_cache", True
        return None, "unavailable", False
    with cache_lock:
        cache = CacheEntry(data=fresh_data, fetched_at=time.monotonic())
        next_provider_attempt_at = 0.0
    return fresh_data, "provider", False


@app.route("/healthz", methods=("GET", "HEAD"))
def healthz() -> Response:
    """Render liveness endpoint; deliberately independent of the data provider."""
    return jsonify({"status": "ok"})


@app.route("/", methods=("GET", "HEAD"))
def calendar() -> Response:
    """Return calendar data or a valid, safe JSON error response."""
    if request.method == "HEAD":
        return Response(status=200, mimetype="application/json")
    data, source, stale = calendar_data()
    if data is None:
        return jsonify(success=False, error="Economic calendar provider temporarily unavailable", data=[]), 503
    payload: dict[str, Any] = {"success": True, "data": data, "source": source}
    if stale:
        payload["warning"] = "Returning recently cached calendar data"
    return jsonify(payload), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
