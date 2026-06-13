import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAM_PREFIXES = ("utm_",)
TRACKING_PARAM_NAMES = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "msclkid",
}


def normalize_url(url: str, strip_tracking_params: bool = True) -> str:
    """Normalize a URL for stable deduplication.

    The scheme and host are lowercased. Default ports are removed. Tracking
    query parameters can be stripped while preserving other query parameters in
    their original order.
    """
    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()

    if not scheme or not hostname:
        raise ValueError("URL must include a scheme and host.")

    netloc = hostname
    if parsed.port and not _is_default_port(scheme, parsed.port):
        netloc = f"{netloc}:{parsed.port}"
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo = f"{userinfo}:{parsed.password}"
        netloc = f"{userinfo}@{netloc}"

    query = parsed.query
    if strip_tracking_params and query:
        query_params = [
            (key, value)
            for key, value in parse_qsl(query, keep_blank_values=True)
            if not _is_tracking_param(key)
        ]
        query = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, parsed.path or "/", query, parsed.fragment))


def hash_long_url(url: str) -> str:
    """Return the SHA-256 hex digest used by links.long_url_hash."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _is_default_port(scheme: str, port: int) -> bool:
    """Return whether port is the default port for scheme."""
    return (scheme == "http" and port == 80) or (scheme == "https" and port == 443)


def _is_tracking_param(name: str) -> bool:
    """Return whether a query parameter is a known tracking parameter."""
    lower_name = name.lower()
    return lower_name in TRACKING_PARAM_NAMES or lower_name.startswith(
        TRACKING_PARAM_PREFIXES
    )
