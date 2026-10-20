"""Where this instance sends its own telemetry, read from the POSTHOG_TELEMETRY_* settings.

Every sender of this instance's own analytics resolves its destination here, so that one pair of
settings and OPT_OUT_CAPTURE decide for the server SDK, the usage reports and the browser alike.
"""

from urllib.parse import urlsplit

from django.conf import settings

from posthog.dataclasses import frozen


@frozen
class TelemetryTarget:
    host: str
    api_key: str


def get_telemetry_target() -> TelemetryTarget | None:
    """The collector to send to, or None when this instance must send nothing.

    A key without a host is not a target: the SDK would fall back to its built-in PostHog Cloud host.
    A host without an http(s) scheme is not a target either: posthog-js reads it as a path on the page's
    own origin, and the CSP cannot name it as a source.
    """
    if settings.OPT_OUT_CAPTURE:
        return None
    host = settings.POSTHOG_TELEMETRY_HOST.strip().rstrip("/")
    api_key = settings.POSTHOG_TELEMETRY_API_KEY.strip()
    if not host or not api_key:
        return None
    parts = urlsplit(host)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None
    return TelemetryTarget(host=host, api_key=api_key)


def get_usage_reports_target() -> TelemetryTarget | None:
    if not settings.POSTHOG_TELEMETRY_USAGE_REPORTS:
        return None
    return get_telemetry_target()
