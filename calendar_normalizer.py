"""Normalize provider payloads to the established API event contract."""

from __future__ import annotations

from typing import Any


COUNTRY_CURRENCIES = {
    "Australia": "AUD", "Canada": "CAD", "Euro Area": "EUR", "Germany": "EUR",
    "Japan": "JPY", "New Zealand": "NZD", "Spain": "EUR", "Switzerland": "CHF",
    "United Kingdom": "GBP", "United States": "USD",
}
IMPACT_LEVELS = {"low": 1, "medium": 2, "med": 2, "high": 3}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def normalize_economicium_events(payload: Any) -> list[dict[str, Any]]:
    """Validate Economicium's public JSON data and keep legacy field names."""
    events = payload.get("data", {}).get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        raise ValueError("events list is missing")

    normalized: list[dict[str, Any]] = []
    for item in events:
        if not isinstance(item, dict):
            raise ValueError("event is not an object")
        date, clock, country, name = (_text(item.get(key)) for key in ("date", "time", "country", "title"))
        impact_name = _text(item.get("impact"))
        if not all((date, clock, country, name, impact_name)) or impact_name.lower() not in IMPACT_LEVELS:
            raise ValueError("event has required fields missing")
        currency = COUNTRY_CURRENCIES.get(country, "")
        # `economy`, `data`, and `name` are retained for existing bot clients.
        normalized.append({
            "economy": currency or country,
            "impact": IMPACT_LEVELS[impact_name.lower()],
            "data": f"{date} {clock}:00",
            "name": name,
            "actual": None,
            "forecast": None,
            "previous": None,
            "date": date,
            "time": clock,
            "country": country,
            "currency": currency or None,
            "event": name,
        })
    return normalized
