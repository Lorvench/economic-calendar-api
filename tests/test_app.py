from app import app, parse_events


SAMPLE_HTML = """
<table id="ecEventsTable">
  <tr id="eventRowId_1" event_timestamp="2018-09-09 22:45:00">
    <td class="flagCur">&nbsp;NZD&nbsp;</td>
    <td class="sentiment"><i class="grayFullBullishIcon"></i><i class="grayFullBullishIcon"></i></td>
    <td class="event">Manufacturing Sales Volume (QoQ) (Q2)</td>
    <td class="act">-1.2%</td><td class="fore">&nbsp;</td><td class="prev">1.4%</td>
  </tr>
  <tr id="eventRowId_2"><td class="flagCur">USD</td><td class="sentiment"></td></tr>
</table>
"""


def test_parse_events_matches_legacy_schema_and_fallbacks():
    assert parse_events(SAMPLE_HTML) == [
        {
            "economy": "NZD", "impact": 2, "data": "2018-09-09 22:45:00",
            "name": "Manufacturing Sales Volume (QoQ) (Q2)", "actual": "-1.2%",
            "forecast": "", "previous": "1.4%",
        },
        {
            "economy": "USD", "impact": 0, "data": None, "name": None,
            "actual": None, "forecast": None, "previous": None,
        },
    ]


def test_root_endpoint_returns_json(monkeypatch):
    expected = [{"economy": "NGN", "impact": 1, "data": None, "name": None,
                 "actual": None, "forecast": None, "previous": None}]
    monkeypatch.setattr("app.fetch_calendar", lambda: expected)

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.get_json() == expected
