import app as calendar_app

SAMPLE_PROVIDER_EVENT = [{"Currency": "NZD", "Importance": 2, "Date": "2018-09-09T22:45:00", "Event": "Manufacturing Sales Volume", "Actual": "-1.2%", "Forecast": "", "Previous": "1.4%"}]


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = SAMPLE_PROVIDER_EVENT if payload is None else payload

    def raise_for_status(self):
        if self.status_code >= 400:
            error = calendar_app.requests.exceptions.HTTPError()
            error.response = self
            raise error

    def json(self):
        return self.payload


def reset_service_state(monkeypatch):
    monkeypatch.setattr(calendar_app, "cache", None)
    monkeypatch.setattr(calendar_app, "next_provider_attempt_at", 0.0)
    monkeypatch.setattr(calendar_app, "FAILURE_BACKOFF_SECONDS", 0)


def test_healthz_get_and_head_are_healthy_without_provider_call(monkeypatch):
    monkeypatch.setattr(calendar_app.http, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))
    client = calendar_app.app.test_client()
    assert client.get("/healthz").get_json() == {"status": "ok"}
    assert client.head("/healthz").status_code == 200


def test_calendar_returns_normalized_provider_data(monkeypatch):
    reset_service_state(monkeypatch)
    monkeypatch.setenv("TRADING_ECONOMICS_API_KEY", "test-key")
    monkeypatch.setattr(calendar_app.http, "get", lambda *_args, **_kwargs: FakeResponse())
    response = calendar_app.app.test_client().get("/")
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert response.get_json()["source"] == "provider"
    assert response.get_json()["data"][0]["economy"] == "NZD"


def test_calendar_returns_valid_json_for_upstream_statuses(monkeypatch):
    for status in (403, 429, 500):
        reset_service_state(monkeypatch)
        monkeypatch.setenv("TRADING_ECONOMICS_API_KEY", "test-key")
        monkeypatch.setattr(calendar_app.http, "get", lambda *_args, status=status, **_kwargs: FakeResponse(status))
        response = calendar_app.app.test_client().get("/")
        assert response.status_code == 503
        assert response.get_json() == {"success": False, "error": "Economic calendar provider temporarily unavailable", "data": []}


def test_calendar_handles_timeout_and_malformed_data(monkeypatch):
    reset_service_state(monkeypatch)
    monkeypatch.setenv("TRADING_ECONOMICS_API_KEY", "test-key")
    monkeypatch.setattr(calendar_app.http, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(calendar_app.requests.exceptions.Timeout()))
    assert calendar_app.app.test_client().get("/").status_code == 503
    reset_service_state(monkeypatch)
    monkeypatch.setattr(calendar_app.http, "get", lambda *_args, **_kwargs: FakeResponse(payload={}))
    assert calendar_app.app.test_client().get("/").status_code == 503


def test_stale_cache_is_returned_when_provider_fails(monkeypatch):
    reset_service_state(monkeypatch)
    monkeypatch.setenv("TRADING_ECONOMICS_API_KEY", "test-key")
    monkeypatch.setattr(calendar_app, "CACHE_TTL_SECONDS", -1)
    monkeypatch.setattr(calendar_app, "STALE_CACHE_TTL_SECONDS", 3600)
    calendar_app.cache = calendar_app.CacheEntry(data=[{"economy": "USD", "impact": 1, "data": None, "name": "Cached", "actual": None, "forecast": None, "previous": None}], fetched_at=calendar_app.time.monotonic())
    monkeypatch.setattr(calendar_app.http, "get", lambda *_args, **_kwargs: FakeResponse(403))
    response = calendar_app.app.test_client().get("/")
    assert response.status_code == 200
    assert response.get_json()["source"] == "stale_cache"
    assert response.get_json()["warning"] == "Returning recently cached calendar data"


def test_root_head_does_not_call_provider(monkeypatch):
    monkeypatch.setattr(calendar_app.http, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))
    response = calendar_app.app.test_client().head("/")
    assert response.status_code == 200
    assert response.data == b""
