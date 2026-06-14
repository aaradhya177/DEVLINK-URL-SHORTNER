import logging

try:
    from ua_parser import user_agent_parser
except ImportError:  # pragma: no cover - optional dependency fallback.
    user_agent_parser = None


logger = logging.getLogger(__name__)


def parse_user_agent(user_agent: str | None) -> dict[str, str | None]:
    """Parse a user-agent into device_type, browser, and os fields."""
    if not user_agent or user_agent_parser is None:
        return {"device_type": None, "browser": None, "os": None}

    try:
        parsed = user_agent_parser.Parse(user_agent)
    except Exception as exc:  # pragma: no cover - parser defensive boundary.
        logger.warning("user_agent_parse_failed", extra={"error": str(exc)})
        return {"device_type": None, "browser": None, "os": None}

    device = parsed.get("device", {})
    browser = parsed.get("user_agent", {})
    os_info = parsed.get("os", {})
    family = device.get("family")
    return {
        "device_type": _device_type(family),
        "browser": browser.get("family"),
        "os": os_info.get("family"),
    }


def _device_type(device_family: str | None) -> str | None:
    """Map parser device family to a coarse device type."""
    if device_family is None:
        return None
    lower_family = device_family.lower()
    if lower_family in {"spider", "bot"}:
        return "bot"
    if "mobile" in lower_family or "phone" in lower_family:
        return "mobile"
    if "tablet" in lower_family or "ipad" in lower_family:
        return "tablet"
    return "desktop"
