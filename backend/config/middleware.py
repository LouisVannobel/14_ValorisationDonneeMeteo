"""
Middleware used by the Django API.
"""

from __future__ import annotations

import time

from django.http import HttpRequest

from .metrics import (
    REQUEST_EXCEPTIONS_TOTAL,
    _get_cached_endpoint_label,
    _record_request,
    _resolve_endpoint_label,
)


class PrometheusMetricsMiddleware:
    """Collect request metrics for the API."""

    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, _view_func, _view_args, _view_kwargs):
        request._prometheus_endpoint = _resolve_endpoint_label(request)

    def __call__(self, request: HttpRequest):
        start_time = time.perf_counter()
        method = request.method.upper()

        try:
            response = self.get_response(request)
        except Exception as exc:
            endpoint = _get_cached_endpoint_label(request)
            _record_request(method, endpoint, 500, start_time)
            REQUEST_EXCEPTIONS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                exception=exc.__class__.__name__,
            ).inc()
            raise

        endpoint = _get_cached_endpoint_label(request)
        _record_request(method, endpoint, response.status_code, start_time)
        return response
