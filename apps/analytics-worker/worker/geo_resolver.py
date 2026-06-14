import logging

from worker.config import settings

try:
    import geoip2.database
except ImportError:  # pragma: no cover - optional dependency fallback.
    geoip2 = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class GeoResolver:
    """Resolve IP addresses with a local GeoLite2 City database when available."""

    def __init__(self) -> None:
        """Create a resolver using GEOIP_DATABASE_PATH if configured."""
        self._reader = None
        if settings.geoip_database_path is None or geoip2 is None:
            logger.warning("geoip_database_unavailable")
            return

        try:
            self._reader = geoip2.database.Reader(settings.geoip_database_path)
        except OSError as exc:
            logger.warning("geoip_database_open_failed", extra={"error": str(exc)})

    def resolve(self, ip_address: str) -> dict[str, str | None]:
        """Return country, region, and city for an IP address, or empty values."""
        if self._reader is None:
            return {"country": None, "region": None, "city": None}

        try:
            result = self._reader.city(ip_address)
        except Exception as exc:  # pragma: no cover - MaxMind can raise many subclasses.
            logger.warning("geoip_lookup_failed", extra={"error": str(exc)})
            return {"country": None, "region": None, "city": None}

        return {
            "country": result.country.iso_code,
            "region": (
                result.subdivisions.most_specific.iso_code
                if result.subdivisions
                else None
            ),
            "city": result.city.name,
        }
