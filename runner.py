"""
runner.py — Core API Test Runner

Executes API tests against configured endpoints and returns
structured results for reporting and display.

Author: Sandrine Uwineza
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from validators import (
    validate_status,   StatusResult,
    validate_schema,   SchemaResult,
    validate_latency,  LatencyResult,
    validate_payload,  PayloadResult,
    validate_required_fields,
    validate_headers,
)


@dataclass
class EndpointResult:
    endpoint_id:    str
    endpoint_name:  str
    method:         str
    url:            str
    passed:         bool
    status:         Optional[StatusResult]  = None
    schema:         Optional[SchemaResult]  = None
    latency:        Optional[LatencyResult] = None
    payload:        Optional[PayloadResult] = None
    headers:        Optional[SchemaResult]  = None
    error:          Optional[str]           = None
    timestamp:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags:           list[str] = field(default_factory=list)

    @property
    def checks_passed(self) -> int:
        checks = [self.status, self.schema, self.latency, self.payload, self.headers]
        return sum(1 for c in checks if c is not None and c.passed)

    @property
    def checks_total(self) -> int:
        checks = [self.status, self.schema, self.latency, self.payload, self.headers]
        return sum(1 for c in checks if c is not None)

    @property
    def summary(self) -> str:
        if self.error:
            return f"❌ Connection Error: {self.error}"
        return f"{'✅' if self.passed else '❌'} {self.checks_passed}/{self.checks_total} checks passed"


@dataclass
class TestSuiteResult:
    name:           str
    base_url:       str
    total:          int
    passed:         int
    failed:         int
    errors:         int
    duration_ms:    float
    results:        list[EndpointResult]
    timestamp:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def pass_rate(self) -> float:
        return round((self.passed / self.total) * 100, 1) if self.total else 0

    @property
    def avg_latency_ms(self) -> Optional[float]:
        latencies = [
            r.latency.latency_ms for r in self.results
            if r.latency is not None
        ]
        return round(sum(latencies) / len(latencies), 2) if latencies else None


def _make_request(
    url:        str,
    method:     str,
    headers:    dict,
    body:       Optional[dict],
    timeout:    int,
) -> tuple[int, dict, dict, float]:
    """
    Execute an HTTP request and return (status, headers, body_dict, latency_ms).
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE

    data = None
    if body:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}

    req = urllib.request.Request(
        url, data=data, headers=headers, method=method.upper()
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            latency_ms = (time.monotonic() - start) * 1000
            status     = resp.status
            resp_headers = dict(resp.headers)
            try:
                body_str  = resp.read().decode("utf-8")
                body_dict = json.loads(body_str)
            except Exception:
                body_dict = {}
            return status, resp_headers, body_dict, latency_ms

    except urllib.error.HTTPError as e:
        latency_ms = (time.monotonic() - start) * 1000
        try:
            body_str  = e.read().decode("utf-8")
            body_dict = json.loads(body_str)
        except Exception:
            body_dict = {}
        return e.code, dict(e.headers), body_dict, latency_ms


def run_endpoint(
    endpoint:        dict,
    base_url:        str,
    default_headers: dict,
    default_timeout: int,
) -> EndpointResult:
    """
    Run all validation checks against a single endpoint definition.
    """
    endpoint_id   = endpoint.get("id",   "unknown")
    endpoint_name = endpoint.get("name", "Unknown")
    method        = endpoint.get("method", "GET").upper()
    path          = endpoint.get("path", "/")
    url           = base_url.rstrip("/") + path
    tags          = endpoint.get("tags", [])

    # Merge headers
    merged_headers = {**default_headers, **endpoint.get("headers", {})}

    # Expected values
    expected_status  = endpoint.get("expected_status",  200)
    expected_schema  = endpoint.get("expected_schema",  {})
    expected_fields  = endpoint.get("expected_fields",  [])
    expected_headers = endpoint.get("expected_headers", {})
    threshold_ms     = endpoint.get("latency_threshold_ms", 2000)
    body             = endpoint.get("body")
    timeout          = endpoint.get("timeout", default_timeout)

    try:
        status_code, resp_headers, resp_body, latency_ms = _make_request(
            url, method, merged_headers, body, timeout
        )
    except Exception as e:
        return EndpointResult(
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            method=method,
            url=url,
            passed=False,
            error=str(e),
            tags=tags,
        )

    # Run validators
    status_result = validate_status(
        endpoint_id, endpoint_name, expected_status, status_code
    )

    schema_result = None
    if expected_schema:
        schema_result = validate_schema(
            endpoint_id, endpoint_name, resp_body, expected_schema
        )

    fields_result = None
    if expected_fields:
        fields_result = validate_required_fields(
            endpoint_id, endpoint_name, resp_body, expected_fields
        )
        # Use fields_result as schema_result if no schema defined
        if schema_result is None:
            schema_result = fields_result

    latency_result = validate_latency(
        endpoint_id, endpoint_name, latency_ms, threshold_ms
    )

    payload_result = validate_payload(
        endpoint_id, endpoint_name, resp_body
    )

    headers_result = None
    if expected_headers:
        headers_result = validate_headers(
            endpoint_id, endpoint_name, resp_headers, expected_headers
        )

    # Determine overall pass/fail
    all_checks = [status_result, schema_result, latency_result, payload_result, headers_result]
    passed = all(c.passed for c in all_checks if c is not None)

    return EndpointResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        method=method,
        url=url,
        passed=passed,
        status=status_result,
        schema=schema_result,
        latency=latency_result,
        payload=payload_result,
        headers=headers_result,
        tags=tags,
    )


def run_suite(
    config:   dict,
    tag:      Optional[str] = None,
    endpoint_ids: Optional[list[str]] = None,
) -> TestSuiteResult:
    """
    Run the full test suite from a config dict.

    Args:
        config:       Parsed endpoints.json config
        tag:          Optional tag filter (e.g. "smoke")
        endpoint_ids: Optional list of endpoint IDs to run

    Returns:
        TestSuiteResult with all endpoint results
    """
    base_url        = config.get("base_url",        "https://httpbin.org")
    default_headers = config.get("default_headers", {})
    default_timeout = config.get("default_timeout", 10)
    endpoints       = config.get("endpoints",       [])
    suite_name      = config.get("name", "API Test Suite")

    # Filter by tag
    if tag:
        endpoints = [e for e in endpoints if tag in e.get("tags", [])]

    # Filter by ID
    if endpoint_ids:
        endpoints = [e for e in endpoints if e.get("id") in endpoint_ids]

    start     = time.monotonic()
    results   = []
    passed    = 0
    failed    = 0
    errors    = 0

    for endpoint in endpoints:
        result = run_endpoint(endpoint, base_url, default_headers, default_timeout)
        results.append(result)
        if result.error:
            errors += 1
        elif result.passed:
            passed += 1
        else:
            failed += 1

    duration_ms = round((time.monotonic() - start) * 1000, 2)

    return TestSuiteResult(
        name=suite_name,
        base_url=base_url,
        total=len(results),
        passed=passed,
        failed=failed,
        errors=errors,
        duration_ms=duration_ms,
        results=results,
    )
