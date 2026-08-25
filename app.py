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

from calendar_provider import CalendarProviderError, EconomiciumProvider

REQUEST_TIMEOUT_SECONDS = float(os.getenv("CALENDAR_REQUEST_TIMEOUT_SECONDS", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CALENDAR_CACHE_TTL_SECONDS", "21600"))
STALE_CACHE_TTL_SECONDS = int(os.getenv("CALENDAR_STALE_CACHE_TTL_SECONDS", "604800"))
FAILURE_BACKOFF_SECONDS = int(os.getenv("CALENDAR_FAILURE_BACKOFF_SECONDS", "120"))

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


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
                  status_forcelist=(500, 502, 503, 504),
                  allowed_methods=frozenset(("GET",)), raise_on_status=False)
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


http = build_http_session()
provider = EconomiciumProvider()


def fetch_calendar() -> list[dict[str, Any]]:
    """Fetch real events through the provider boundary."""
    return provider.fetch_calendar(http, REQUEST_TIMEOUT_SECONDS)


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
    except CalendarProviderError as error:
        with cache_lock:
            retry_after = error.retry_after if error.retry_after is not None else FAILURE_BACKOFF_SECONDS
            next_provider_attempt_at = time.monotonic() + max(FAILURE_BACKOFF_SECONDS, retry_after)
            if cache and now - cache.fetched_at < STALE_CACHE_TTL_SECONDS:
                return cache.data, "stale_cache", True
        return None, "unavailable", False
    with cache_lock:
        cache = CacheEntry(data=fresh_data, fetched_at=time.monotonic())
        next_provider_attempt_at = 0.0
    return fresh_data, "provider", False


@app.route("/healthz", methods=("GET", "HEAD"))
def healthz() -> tuple[dict[str, str], int]:
    """Render liveness endpoint; deliberately independent of the data provider."""
    return {"status": "ok"}, 200


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
