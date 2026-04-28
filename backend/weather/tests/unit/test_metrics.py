from __future__ import annotations

from django.urls import reverse
from prometheus_client.parser import text_string_to_metric_families
from rest_framework.test import APIClient


def _sample_value(metrics_text: str, sample_name: str, labels: dict[str, str]) -> float:
    for family in text_string_to_metric_families(metrics_text):
        for sample in family.samples:
            if sample.name == sample_name and sample.labels == labels:
                return float(sample.value)

    return 0.0


def test_metrics_endpoint_exposes_request_metrics(client: APIClient):
    response = client.get(reverse("metrics"))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")

    body = response.content.decode()
    assert "meteo_api_http_requests_total" in body
    assert "meteo_api_http_request_duration_seconds" in body
    assert "meteo_api_http_request_exceptions_total" in body


def test_api_request_increments_request_counter(client: APIClient):
    metrics_url = reverse("metrics")
    records_url = reverse("records")
    expected_labels = {
        "method": "GET",
        "endpoint": "records",
        "status_code": "200",
    }

    before_response = client.get(metrics_url)
    before_count = _sample_value(
        before_response.content.decode(),
        "meteo_api_http_requests_total",
        expected_labels,
    )

    api_response = client.get(
        records_url,
        {
            "date_start": "2024-01-01",
            "date_end": "2024-12-31",
        },
    )

    assert api_response.status_code == 200

    after_response = client.get(metrics_url)
    after_count = _sample_value(
        after_response.content.decode(),
        "meteo_api_http_requests_total",
        expected_labels,
    )

    assert after_count == before_count + 1