"""Provider boundary for the free economic-calendar data source."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

from calendar_normalizer import normalize_economicium_events


ECONOMICIUM_CALENDAR_URL = "https://www.economicium.com/data/economic-calendar.json"
logger = logging.getLogger(__name__)


class CalendarProviderError(Exception):
    """Safe error raised when a calendar provider cannot supply valid data."""

    def __init__(self, message: str = "Economic calendar provider temporarily unavailable", *, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


def _retry_after_seconds(response: requests.Response) -> int | None:
    value = response.headers.get("Retry-After")
    try:
        return max(0, int(value)) if value is not None else None
    except ValueError:
        return None


@dataclass(frozen=True)
class EconomiciumProvider:
    """Keyless JSON feed compiled from official release calendars.

    The feed supplies upcoming release schedules, country, UTC time and impact.
    It does not publish commercial consensus forecasts or live result values.
    """

    url: str = ECONOMICIUM_CALENDAR_URL

    def fetch_calendar(self, http: requests.Session, timeout: float) -> list[dict[str, Any]]:
        try:
            response = http.get(
                self.url,
                headers={"Accept": "application/json", "User-Agent": "economic-calendar-api/1.0"},
                timeout=timeout,
            )
        except requests.exceptions.Timeout as error:
            raise CalendarProviderError() from error
        except requests.exceptions.RequestException as error:
            raise CalendarProviderError() from error

        if response.status_code == 429:
            raise CalendarProviderError(retry_after=_retry_after_seconds(response))
        if response.status_code >= 400:
            raise CalendarProviderError()

        try:
            return normalize_economicium_events(response.json())
        except (TypeError, ValueError, KeyError) as error:
            logger.warning("Economicium returned invalid JSON/schema")
            raise CalendarProviderError() from error
