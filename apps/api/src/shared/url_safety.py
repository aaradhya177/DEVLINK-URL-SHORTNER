import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)
GOOGLE_SAFE_BROWSING_ENDPOINT = (
    "https://safebrowsing.googleapis.com/v4/threatMatches:find"
)
GOOGLE_TEST_URL_HOST = "testsafebrowsing.appspot.com"


@dataclass(frozen=True, slots=True)
class UrlSafetyResult:
    """Result of checking a URL against a safety provider."""

    is_malicious: bool
    reason: str | None = None
    checked: bool = True


class UrlSafetyProvider(Protocol):
    """Interface for pluggable URL safety providers."""

    async def check_url(self, url: str) -> UrlSafetyResult:
        """Check a URL and return whether it is known malicious."""


class GoogleSafeBrowsingProvider:
    """Google Safe Browsing v4 Lookup API provider."""

    def __init__(self, api_key: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def check_url(self, url: str) -> UrlSafetyResult:
        """Check one URL using Google's threatMatches:find endpoint."""
        if _is_google_test_url(url):
            return UrlSafetyResult(True, "google_safe_browsing_test_url")

        payload = {
            "client": {
                "clientId": "devlink",
                "clientVersion": "0.1.0",
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                GOOGLE_SAFE_BROWSING_ENDPOINT,
                params={"key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        matches = data.get("matches") or []
        if not matches:
            return UrlSafetyResult(False)

        threat_types = sorted(
            {
                str(match.get("threatType"))
                for match in matches
                if match.get("threatType")
            }
        )
        reason = "google_safe_browsing:" + ",".join(threat_types)
        return UrlSafetyResult(True, reason)


class NoopUrlSafetyProvider:
    """Development fallback when no external provider is configured."""

    async def check_url(self, url: str) -> UrlSafetyResult:
        """Return a local test result or mark the URL as unchecked."""
        if _is_google_test_url(url):
            return UrlSafetyResult(True, "google_safe_browsing_test_url")
        return UrlSafetyResult(False, checked=False)


def get_url_safety_provider() -> UrlSafetyProvider:
    """Return the configured URL safety provider."""
    if settings.google_safe_browsing_api_key:
        return GoogleSafeBrowsingProvider(
            settings.google_safe_browsing_api_key,
            settings.url_safety_timeout_seconds,
        )
    return NoopUrlSafetyProvider()


async def check_url_safety(url: str) -> UrlSafetyResult:
    """Check URL safety and fail open on provider failure or timeout.

    Link creation should not be held hostage by a third-party outage. On timeout
    or provider error we leave the link active with checked=False so a scheduled
    retry can re-check it later.
    """
    provider = get_url_safety_provider()
    try:
        return await asyncio.wait_for(
            provider.check_url(url),
            timeout=settings.url_safety_timeout_seconds + 0.1,
        )
    except (httpx.HTTPError, TimeoutError, asyncio.TimeoutError) as exc:
        logger.warning("url_safety_check_failed", extra={"error": str(exc)})
        return UrlSafetyResult(False, checked=False)


def _is_google_test_url(url: str) -> bool:
    """Return whether a URL is one of Google's Safe Browsing test URLs."""
    return GOOGLE_TEST_URL_HOST in url.lower()
