"""
payload_validator.py — HTTP Request/Response Payload Validator

Validates request and response payload integrity — checks for
null values, empty strings, data consistency, and payload size.

Author: Sandrine Uwineza
"""

import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PayloadResult:
    endpoint_id:   str
    endpoint_name: str
    passed:        bool
    issues:        list[str] = field(default_factory=list)
    info:          list[str] = field(default_factory=list)
    payload_size_bytes: int = 0

    @property
    def message(self) -> str:
        if self.passed:
            return (
                f"✅ Payload valid — "
                f"{self.payload_size_bytes} bytes, "
                f"no integrity issues."
            )
        return f"❌ Payload issues found — {len(self.issues)} problem(s)."


def validate_payload(
    endpoint_id:   str,
    endpoint_name: str,
    response_body: Any,
    check_nulls:   bool = True,
    check_empty:   bool = True,
    max_size_kb:   int  = 1024,
) -> PayloadResult:
    """
    Validate the integrity of a JSON response payload.

    Checks:
    - Null values in critical fields
    - Empty strings where values are expected
    - Payload size within acceptable bounds
    - Valid JSON structure

    Args:
        endpoint_id:   Unique endpoint identifier
        endpoint_name: Human-readable name
        response_body: Parsed JSON response
        check_nulls:   Flag null values as issues
        check_empty:   Flag empty strings as issues
        max_size_kb:   Maximum acceptable payload size in KB

    Returns:
        PayloadResult with pass/fail and list of issues
    """
    issues = []
    info   = []

    # Measure payload size
    try:
        payload_str        = json.dumps(response_body)
        payload_bytes      = len(payload_str.encode("utf-8"))
        payload_size_bytes = payload_bytes
    except (TypeError, ValueError):
        return PayloadResult(
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            passed=False,
            issues=["Response body is not JSON-serializable"],
        )

    # Check payload size
    payload_size_kb = payload_bytes / 1024
    info.append(f"Payload size: {payload_bytes} bytes ({payload_size_kb:.2f} KB)")

    if payload_size_kb > max_size_kb:
        issues.append(
            f"Payload size {payload_size_kb:.2f} KB exceeds "
            f"maximum {max_size_kb} KB"
        )

    # Check for nulls and empty strings in dict payloads
    if isinstance(response_body, dict):
        null_fields  = []
        empty_fields = []

        for key, value in response_body.items():
            if check_nulls and value is None:
                null_fields.append(key)
            if check_empty and isinstance(value, str) and value.strip() == "":
                empty_fields.append(key)

        if null_fields:
            issues.append(f"Null values found in fields: {', '.join(null_fields)}")

        if empty_fields:
            issues.append(f"Empty string values in fields: {', '.join(empty_fields)}")

        info.append(f"Total fields in response: {len(response_body)}")

    elif isinstance(response_body, list):
        info.append(f"Response is array with {len(response_body)} items")
        if len(response_body) == 0:
            issues.append("Response array is empty")

    return PayloadResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        passed=len(issues) == 0,
        issues=issues,
        info=info,
        payload_size_bytes=payload_size_bytes,
    )


def compare_payloads(
    payload_a: Any,
    payload_b: Any,
    ignore_keys: list[str] = None,
) -> dict:
    """
    Compare two JSON payloads and return a diff summary.
    Useful for regression testing — comparing responses across runs.
    """
    ignore_keys = ignore_keys or []

    if not isinstance(payload_a, dict) or not isinstance(payload_b, dict):
        return {
            "match": payload_a == payload_b,
            "differences": [] if payload_a == payload_b else ["Non-dict payloads differ"]
        }

    differences = []
    all_keys    = set(payload_a.keys()) | set(payload_b.keys())

    for key in all_keys:
        if key in ignore_keys:
            continue
        if key not in payload_a:
            differences.append(f"Key '{key}' missing from payload A")
        elif key not in payload_b:
            differences.append(f"Key '{key}' missing from payload B")
        elif payload_a[key] != payload_b[key]:
            differences.append(
                f"Key '{key}' differs: "
                f"A={payload_a[key]!r}, B={payload_b[key]!r}"
            )

    return {
        "match":       len(differences) == 0,
        "differences": differences,
        "keys_in_a":   len(payload_a),
        "keys_in_b":   len(payload_b),
    }
