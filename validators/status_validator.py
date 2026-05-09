"""
status_validator.py — HTTP Status Code Validator

Validates that API responses return the expected HTTP status codes.
Handles 2xx success, 3xx redirects, 4xx client errors, 5xx server errors.

Author: Sandrine Uwineza
"""

from dataclasses import dataclass
from typing import Optional


# HTTP Status code descriptions
STATUS_DESCRIPTIONS = {
    200: "OK", 201: "Created", 202: "Accepted",
    204: "No Content", 206: "Partial Content",
    301: "Moved Permanently", 302: "Found",
    304: "Not Modified", 307: "Temporary Redirect",
    400: "Bad Request", 401: "Unauthorized",
    403: "Forbidden", 404: "Not Found",
    405: "Method Not Allowed", 408: "Request Timeout",
    409: "Conflict", 422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error", 502: "Bad Gateway",
    503: "Service Unavailable", 504: "Gateway Timeout",
}

STATUS_CATEGORIES = {
    "1xx": "Informational",
    "2xx": "Success",
    "3xx": "Redirection",
    "4xx": "Client Error",
    "5xx": "Server Error",
}


@dataclass
class StatusResult:
    endpoint_id:     str
    endpoint_name:   str
    expected_status: int
    actual_status:   int
    passed:          bool
    message:         str
    category:        str

    @property
    def status_description(self) -> str:
        return STATUS_DESCRIPTIONS.get(self.actual_status, f"HTTP {self.actual_status}")


def get_status_category(code: int) -> str:
    """Return the category of an HTTP status code."""
    if 100 <= code < 200:
        return "1xx — Informational"
    elif 200 <= code < 300:
        return "2xx — Success"
    elif 300 <= code < 400:
        return "3xx — Redirection"
    elif 400 <= code < 500:
        return "4xx — Client Error"
    elif 500 <= code < 600:
        return "5xx — Server Error"
    return "Unknown"


def validate_status(
    endpoint_id:     str,
    endpoint_name:   str,
    expected_status: int,
    actual_status:   int,
) -> StatusResult:
    """
    Validate that the actual HTTP status code matches the expected one.

    Args:
        endpoint_id:     Unique identifier for the endpoint
        endpoint_name:   Human-readable name
        expected_status: The status code we expect
        actual_status:   The status code we received

    Returns:
        StatusResult with pass/fail and descriptive message
    """
    passed  = actual_status == expected_status
    category = get_status_category(actual_status)

    if passed:
        message = (
            f"✅ Status code {actual_status} "
            f"({STATUS_DESCRIPTIONS.get(actual_status, 'Unknown')}) "
            f"matches expected."
        )
    else:
        message = (
            f"❌ Expected status {expected_status} "
            f"({STATUS_DESCRIPTIONS.get(expected_status, 'Unknown')}) "
            f"but received {actual_status} "
            f"({STATUS_DESCRIPTIONS.get(actual_status, 'Unknown')})."
        )

    return StatusResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        expected_status=expected_status,
        actual_status=actual_status,
        passed=passed,
        message=message,
        category=category,
    )


def is_success(status_code: int) -> bool:
    """Return True if the status code indicates success (2xx)."""
    return 200 <= status_code < 300


def is_client_error(status_code: int) -> bool:
    """Return True if the status code indicates a client error (4xx)."""
    return 400 <= status_code < 500


def is_server_error(status_code: int) -> bool:
    """Return True if the status code indicates a server error (5xx)."""
    return 500 <= status_code < 600
