(Forex) Economic Calendar API
==========================
[![Python tests](https://github.com/andrevlima/economic-calendar-api/actions/workflows/python.yml/badge.svg?branch=master)](https://github.com/andrevlima/economic-calendar-api/actions/workflows/python.yml)

This project consists of a Python-based API endpoint designed to rapidly deliver the current economic calendar of events in JSON format, often utilized within the Forex market.

It uses the documented Trading Economics economic-calendar API. Set the
`TRADING_ECONOMICS_API_KEY` environment variable to a valid key; do not commit it.
The service caches valid responses and remains healthy when the provider is
temporarily unavailable.

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
set TRADING_ECONOMICS_API_KEY=your-key # PowerShell: $env:TRADING_ECONOMICS_API_KEY="your-key"
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
    "economy": "NZD",
    "impact": 1,
    "data": "2018-09-09 22:45:00",
    "name": "Manufacturing Sales Volume (QoQ) (Q2)",
    "actual": "-1.2%",
    "forecast": "",
    "previous": "1.4%"
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
- Secret environment variable: `TRADING_ECONOMICS_API_KEY`

`GET` and `HEAD /healthz` always return `200` without calling the calendar
provider. `GET /` returns cached data during a transient provider failure, or a
safe JSON `503` response with an empty `data` list when no cache is available.

## Demo
A demo available is [here](https://andrevlimawebh.000webhostapp.com/) (Can be broken, free server can be deleted)

Tip: If you want, you are able to host it in almost free webhosts to make it online and available on the internet. 
https://www.freehosting.com/ or https://www.000webhost.com/ and many others.
