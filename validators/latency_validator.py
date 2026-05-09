"""
latency_validator.py — API Response Latency Validator

Validates that API endpoints respond within defined SLA thresholds.
Categorises latency into performance tiers and flags slow responses.

Author: Sandrine Uwineza
"""

from dataclasses import dataclass
from typing import Optional


# Performance tiers in milliseconds
LATENCY_TIERS = {
    "excellent": (0,    100),
    "good":      (100,  300),
    "acceptable":(300,  1000),
    "slow":      (1000, 3000),
    "critical":  (3000, float("inf")),
}

TIER_COLORS = {
    "excellent":  "#10b981",   # green
    "good":       "#3b82f6",   # blue
    "acceptable": "#f59e0b",   # yellow
    "slow":       "#f97316",   # orange
    "critical":   "#ef4444",   # red
}


@dataclass
class LatencyResult:
    endpoint_id:       str
    endpoint_name:     str
    latency_ms:        float
    threshold_ms:      float
    passed:            bool
    tier:              str
    message:           str

    @property
    def tier_color(self) -> str:
        return TIER_COLORS.get(self.tier, "#94a3b8")

    @property
    def within_threshold(self) -> bool:
        return self.latency_ms <= self.threshold_ms


def classify_latency(latency_ms: float) -> str:
    """Classify latency into a performance tier."""
    for tier, (low, high) in LATENCY_TIERS.items():
        if low <= latency_ms < high:
            return tier
    return "critical"


def validate_latency(
    endpoint_id:   str,
    endpoint_name: str,
    latency_ms:    float,
    threshold_ms:  float = 2000,
) -> LatencyResult:
    """
    Validate that the response latency is within the defined threshold.

    Args:
        endpoint_id:   Unique endpoint identifier
        endpoint_name: Human-readable name
        latency_ms:    Actual measured response time in milliseconds
        threshold_ms:  Maximum acceptable response time in milliseconds

    Returns:
        LatencyResult with pass/fail and performance tier
    """
    passed = latency_ms <= threshold_ms
    tier   = classify_latency(latency_ms)

    if passed:
        message = (
            f"✅ Response time {latency_ms:.0f}ms is within "
            f"threshold ({threshold_ms:.0f}ms). "
            f"Performance: {tier.upper()}."
        )
    else:
        overage = latency_ms - threshold_ms
        message = (
            f"❌ Response time {latency_ms:.0f}ms exceeds "
            f"threshold ({threshold_ms:.0f}ms) by {overage:.0f}ms. "
            f"Performance: {tier.upper()}."
        )

    return LatencyResult(
        endpoint_id=endpoint_id,
        endpoint_name=endpoint_name,
        latency_ms=round(latency_ms, 2),
        threshold_ms=threshold_ms,
        passed=passed,
        tier=tier,
        message=message,
    )


def summarise_latencies(results: list[LatencyResult]) -> dict:
    """Return aggregated latency statistics across all results."""
    if not results:
        return {}

    times = [r.latency_ms for r in results]
    return {
        "count":   len(times),
        "min_ms":  round(min(times), 2),
        "max_ms":  round(max(times), 2),
        "avg_ms":  round(sum(times) / len(times), 2),
        "passed":  sum(1 for r in results if r.passed),
        "failed":  sum(1 for r in results if not r.passed),
        "tiers":   {tier: sum(1 for r in results if r.tier == tier)
                    for tier in LATENCY_TIERS},
    }
