(Forex) Economic Calendar API
==========================
[![Python tests](https://github.com/andrevlima/economic-calendar-api/actions/workflows/python.yml/badge.svg?branch=master)](https://github.com/andrevlima/economic-calendar-api/actions/workflows/python.yml)

This project consists of a Python-based API endpoint designed to rapidly deliver the current economic calendar of events in JSON format, often utilized within the Forex market.

It uses Economicium's free, keyless JSON economic-release calendar:
`https://www.economicium.com/data/economic-calendar.json`. The data is compiled
from official national statistics agencies and central-bank release schedules.
It includes the published event date/time, country and impact; it deliberately
does not redistribute commercial consensus forecasts or live release results, so
`actual`, `forecast`, and `previous` are returned as `null`.

No API key, subscription, or credit card is required. Responses are cached for
six hours (configurable) and stale real data can be served for seven days during
a provider outage.

The API has been intentionally developed with simplicity in mind, both in terms of maintenance and usability, ensuring that it remains straightforward to integrate into various applications.

![Static Badge](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)

## Play / Installation 
Create and activate a virtual environment, install the dependencies, then run the
application:

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

## How to use:

Once the service is running, the endpoint is available at:

```
http://localhost:8000/
```
And you will see a JSON response like this:
```json
{
  "success": true,
  "data": [
    {
    "economy": "USD",
    "impact": 3,
    "data": "2026-08-26 12:30:00",
    "name": "US GDP (Gross Domestic Product)",
    "actual": null,
    "forecast": null,
    "previous": null,
    "country": "United States",
    "currency": "USD"
    }
  ]
}
```

## Render deployment

The included `render.yaml` defines the required configuration. If configuring in
the Render Dashboard instead, create a **Web Service** and set:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Health-check path: `/healthz`
- No provider secret is required.

`GET` and `HEAD /healthz` always return `200` without calling the calendar
provider. `GET /` returns cached data during a transient provider failure, or a
safe JSON `503` response with an empty `data` list when no cache is available.

Economicium publishes its JSON files without a key or documented rate limit;
the six-hour cache keeps this service well below reasonable-use traffic. HTTP
429 honours `Retry-After` and otherwise backs off before another provider call.

## Demo
A demo available is [here](https://andrevlimawebh.000webhostapp.com/) (Can be broken, free server can be deleted)

Tip: If you want, you are able to host it in almost free webhosts to make it online and available on the internet. 
https://www.freehosting.com/ or https://www.000webhost.com/ and many others.
