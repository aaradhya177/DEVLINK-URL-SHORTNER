import pytest

from src.shared.url_utils import hash_long_url, normalize_url, validate_safe_redirect_url


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        (" HTTPS://Example.COM ", "https://example.com/"),
        ("https://example.com", "https://example.com/"),
        ("https://example.com/", "https://example.com/"),
        ("http://example.com:80/a", "http://example.com/a"),
        ("https://example.com:443/a", "https://example.com/a"),
        ("https://example.com:8443/a", "https://example.com:8443/a"),
        (
            "https://Example.com/a?utm_source=x&b=2&gclid=y&a=1",
            "https://example.com/a?b=2&a=1",
        ),
        (
            "https://example.com/a?b=2&a=1",
            "https://example.com/a?b=2&a=1",
        ),
    ],
)
def test_normalize_url(raw_url: str, expected: str) -> None:
    """Normalization should stabilize dedup-sensitive URL parts."""
    assert normalize_url(raw_url) == expected


def test_normalize_url_can_preserve_tracking_params() -> None:
    """Tracking stripping should be optional."""
    assert (
        normalize_url(
            "https://example.com/?utm_source=x&b=2",
            strip_tracking_params=False,
        )
        == "https://example.com/?utm_source=x&b=2"
    )


def test_normalize_url_preserves_path_case_and_fragment() -> None:
    """Path case can be meaningful and should not be lowercased."""
    assert (
        normalize_url("https://EXAMPLE.com/CaseSensitive#Part")
        == "https://example.com/CaseSensitive#Part"
    )


def test_normalize_url_rejects_relative_url() -> None:
    """Only absolute HTTP(S)-style URLs should reach link creation."""
    with pytest.raises(ValueError):
        normalize_url("/relative/path")


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://localhost/admin",
        "http://LOCALHOST./admin",
        "http://app.localhost/admin",
        "http://127.0.0.1/admin",
        "http://10.0.0.1/admin",
        "http://172.16.0.1/admin",
        "http://192.168.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/admin",
    ],
)
def test_validate_safe_redirect_url_rejects_ssrf_targets(url: str) -> None:
    """Redirect targets should reject localhost, private IPs, and non-HTTP schemes."""
    with pytest.raises(ValueError):
        validate_safe_redirect_url(url)


def test_validate_safe_redirect_url_allows_public_http_url() -> None:
    """Public HTTP(S) targets should be accepted."""
    assert validate_safe_redirect_url("https://example.com/path") == "https://example.com/path"


def test_hash_long_url_is_stable_sha256() -> None:
    """URL hashes should be stable SHA-256 hex digests."""
    first = hash_long_url("https://example.com/")
    second = hash_long_url("https://example.com/")

    assert first == second
    assert len(first) == 64
    assert first != hash_long_url("https://example.com/a")
