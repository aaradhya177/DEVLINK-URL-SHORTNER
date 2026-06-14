import httpx

from src.shared import url_safety
from src.shared.url_safety import (
    GoogleSafeBrowsingProvider,
    NoopUrlSafetyProvider,
    UrlSafetyResult,
    check_url_safety,
)


async def test_noop_provider_flags_google_test_url() -> None:
    """Local development can still verify the malicious URL path."""
    result = await NoopUrlSafetyProvider().check_url(
        "http://testsafebrowsing.appspot.com/apiv4/ANY_PLATFORM/MALWARE/URL/"
    )

    assert result == UrlSafetyResult(
        is_malicious=True,
        reason="google_safe_browsing_test_url",
        checked=True,
    )


async def test_noop_provider_marks_regular_url_unchecked() -> None:
    """Without an API key, ordinary URLs should fail open for scheduled retry."""
    result = await NoopUrlSafetyProvider().check_url("https://example.com")

    assert result.is_malicious is False
    assert result.reason is None
    assert result.checked is False


async def test_google_provider_parses_threat_matches(monkeypatch) -> None:
    """Google matches should become a deterministic flagged reason."""
    requests: list[dict[str, object]] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "matches": [
                    {"threatType": "SOCIAL_ENGINEERING"},
                    {"threatType": "MALWARE"},
                ]
            }

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(
            self,
            endpoint: str,
            params: dict[str, str],
            json: dict[str, object],
        ) -> FakeResponse:
            requests.append({"endpoint": endpoint, "params": params, "json": json})
            return FakeResponse()

    monkeypatch.setattr(url_safety.httpx, "AsyncClient", FakeClient)

    result = await GoogleSafeBrowsingProvider(
        api_key="safe-browsing-key",
        timeout_seconds=0.2,
    ).check_url("https://bad.example")

    assert result.is_malicious is True
    assert result.reason == "google_safe_browsing:MALWARE,SOCIAL_ENGINEERING"
    assert result.checked is True
    assert requests[0]["params"] == {"key": "safe-browsing-key"}
    threat_info = requests[0]["json"]["threatInfo"]  # type: ignore[index]
    assert threat_info["threatEntries"] == [{"url": "https://bad.example"}]


async def test_check_url_safety_fails_open_on_provider_error(monkeypatch) -> None:
    """Provider outages should not block link creation."""

    class BrokenProvider:
        async def check_url(self, _: str) -> UrlSafetyResult:
            raise httpx.TimeoutException("provider timed out")

    monkeypatch.setattr(url_safety, "get_url_safety_provider", lambda: BrokenProvider())

    result = await check_url_safety("https://example.com")

    assert result.is_malicious is False
    assert result.reason is None
    assert result.checked is False
