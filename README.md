(Forex) Economic Calendar API
==========================
[![Python tests](https://github.com/andrevlima/economic-calendar-api/actions/workflows/python.yml/badge.svg?branch=master)](https://github.com/andrevlima/economic-calendar-api/actions/workflows/python.yml)

This project consists of a Python-based API endpoint designed to rapidly deliver the current economic calendar of events in JSON format, often utilized within the Forex market.

It sources its data from investing.com through web crawling techniques, extracting relevant information and presenting it in a well-structured data model, specifically in JSON format.
It is important to note that there are no guarantees regarding its availability or stability. Potential changes on the source page (investing.com) could disrupt the web crawler's functionality, leading to possible outages or errors.

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
And you will see a JSON as response like this:
```json
[
  {
    "economy": "NZD",
    "impact": 1,
    "data": "2018-09-09 22:45:00",
    "name": "Manufacturing Sales Volume (QoQ) (Q2)",
    "actual": "-1.2%",
    "forecast": "",
    "previous": "1.4%"
  },
  ...
]
```

## Demo
A demo available is [here](https://andrevlimawebh.000webhostapp.com/) (Can be broken, free server can be deleted)

Tip: If you want, you are able to host it in almost free webhosts to make it online and available on the internet. 
https://www.freehosting.com/ or https://www.000webhost.com/ and many others.
