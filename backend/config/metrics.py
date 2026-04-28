"""
Prometheus metrics for the Django API.
"""

from __future__ import annotations

import re
import time

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_safe
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    GCCollector,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)

REGISTRY = CollectorRegistry(auto_describe=True)
ProcessCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)
GCCollector(registry=REGISTRY)

REQUEST_DURATION_SECONDS = Histogram(
    "meteo_api_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("method", "endpoint"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

REQUESTS_TOTAL = Counter(
    "meteo_api_http_requests_total",
    "Total HTTP requests handled by the API.",
    labelnames=("method", "endpoint", "status_code"),
    registry=REGISTRY,
)

REQUEST_EXCEPTIONS_TOTAL = Counter(
    "meteo_api_http_request_exceptions_total",
    "Unhandled exceptions raised while processing HTTP requests.",
    labelnames=("method", "endpoint", "exception"),
    registry=REGISTRY,
)

_UUID_SEGMENT = re.compile(
    r"(?<=/)[0-9a-fA-F]{8,}(?:-[0-9a-fA-F]{4,}){3}-[0-9a-fA-F]{12}(?=/|$)"
)
_NUMERIC_SEGMENT = re.compile(r"(?<=/)\d+(?=/|$)")


def _sanitize_path(path: str) -> str:
    normalized = path.strip("/")
    if not normalized:
        return "root"

    normalized = _UUID_SEGMENT.sub(":uuid", normalized)
    normalized = _NUMERIC_SEGMENT.sub(":id", normalized)
    return normalized


def _resolve_endpoint_label(request: HttpRequest) -> str:
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is not None:
        view_name = getattr(resolver_match, "view_name", None)
        if view_name:
            return view_name

        route = getattr(resolver_match, "route", None)
        if route:
            return _sanitize_path(route)

    return _sanitize_path(getattr(request, "path_info", "/"))


def _get_cached_endpoint_label(request: HttpRequest) -> str:
    cached = getattr(request, "_prometheus_endpoint", None)
    if cached is not None:
        return cached
    return _resolve_endpoint_label(request)


def _record_request(method: str, endpoint: str, status_code: int, start_time: float) -> None:
    REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(
        max(0.0, time.perf_counter() - start_time)
    )
    REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()


@require_safe
def metrics_view(request: HttpRequest) -> HttpResponse:
    response = HttpResponse(generate_latest(REGISTRY), content_type=CONTENT_TYPE_LATEST)
    response["Cache-Control"] = "no-store"
    return response
