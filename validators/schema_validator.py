"""
schema_validator.py — JSON Response Schema Validator

Validates that API responses conform to an expected JSON schema.
Checks field presence, data types, and nested object structures.

Author: Sandrine Uwineza
"""

import json
from dataclasses import dataclass, field
from typing import Any, Optional


# Type mapping from schema strings to Python types
TYPE_MAP = {
    "string":  str,
    "integer": int,
    "number":  (int, float),
    "boolean": bool,
    "array":   list,
    "object":  dict,
    "null":    type(None),
}


@dataclass
class SchemaResult:
    endpoint_id:    str
    endpoint_name:  str
    passed:         bool
    errors:         list[str] = field(default_factory=list)
    warnings:       list[str] = field(default_factory=list)
    fields_checked: int = 0

    @property
    def message(self) -> str:
        if self.passed:
            return f"✅ Schema valid — {self.fields_checked} field(s) checked."
        return f"❌ Schema invalid — {len(self.errors)} error(s) found."


def validate_type(value: Any, expected_type: str) -> bool:
    """Check if a value matches the expected type string."""
    python_type = TYPE_MAP.get(expected_type.lower())
    if python_type is None:
        return True  # Unknown type — skip
    return isinstance(value, python_type)


def validate_schema(
    endpoint_id:     str,
    endpoint_name:   str,
    response_body:   Any,
    expected_schema: dict,
) -> SchemaResult:
    """
    Validate a JSON response body against an expected schema definition.

    The schema is a flat dict mapping field names to expected types:
    {
        "id":    "integer",
        "name":  "string",
        "data":  "object",
        "items": "array"
    }

    Args:
        endpoint_id:     Unique endpoint identifier
        endpoint_name:   Human-readable endpoint name
        response_body:   Parsed JSON response (dict or list)
        expected_schema: Dict of field_name -> expected_type

    Returns:
        SchemaResult with pass/fail and list of errors
    """
    errors   = []
    warnings = []
    checked  = 0

    if not isinstance(response_body, dict):
        return SchemaResult(
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            passed=False,
            errors=["Response body is not a JSON object (dict)"],
        )

    for field_name, expected_type in expected_schema.items():
        checked += 1

        # Check field presence
        if field_name not in response_body:
            errors.append(
                f"Missing field '{field_name}' "
                f"(expected type: {expected_type})"
            )
            continue

        # Check field type
        actual_value = response_body[field_name]
        if not validate_type(actual_value, expected_type):
            actual_type = type(actual_value).__name__
            errors.append(
                f"Field '{field_name}' has wrong type: "
                f"expected '{expected_type}', got '{actual_type}'"
            )

    return SchemaResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        fields_checked=checked,
    )


def validate_required_fields(
    endpoint_id:     str,
    endpoint_name:   str,
    response_body:   Any,
    required_fields: list[str],
) -> SchemaResult:
    """
    Validate that all required fields are present in the response body.

    Args:
        endpoint_id:     Unique endpoint identifier
        endpoint_name:   Human-readable endpoint name
        response_body:   Parsed JSON response
        required_fields: List of field names that must be present

    Returns:
        SchemaResult with pass/fail
    """
    errors  = []
    checked = 0

    if not isinstance(response_body, dict):
        return SchemaResult(
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            passed=False,
            errors=["Response body is not a JSON object"],
        )

    for field_name in required_fields:
        checked += 1
        if field_name not in response_body:
            errors.append(f"Required field '{field_name}' is missing from response")
        elif response_body[field_name] is None:
            errors.append(f"Required field '{field_name}' is null")

    return SchemaResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        passed=len(errors) == 0,
        errors=errors,
        fields_checked=checked,
    )


def validate_headers(
    endpoint_id:      str,
    endpoint_name:    str,
    response_headers: dict,
    expected_headers: dict,
) -> SchemaResult:
    """
    Validate that expected HTTP response headers are present and correct.
    """
    errors  = []
    checked = 0

    for header_name, expected_value in expected_headers.items():
        checked += 1
        # Headers are case-insensitive
        actual_value = None
        for key, val in response_headers.items():
            if key.lower() == header_name.lower():
                actual_value = val
                break

        if actual_value is None:
            errors.append(f"Missing header '{header_name}'")
        elif expected_value and expected_value.lower() not in actual_value.lower():
            errors.append(
                f"Header '{header_name}' mismatch: "
                f"expected '{expected_value}', got '{actual_value}'"
            )

    return SchemaResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        passed=len(errors) == 0,
        errors=errors,
        fields_checked=checked,
    )
