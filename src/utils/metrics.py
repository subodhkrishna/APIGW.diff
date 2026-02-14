"""Metrics collection and calculation utilities."""

import statistics
from typing import List


class MetricsCollector:
    """Collects and calculates performance metrics from latency measurements."""

    def __init__(self):
        """Initialize metrics collector."""
        self.latencies: List[float] = []
        self.errors: List[str] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def add_latency(self, latency_ms: float):
        """Add a latency measurement.

        Args:
            latency_ms: Latency in milliseconds
        """
        self.latencies.append(latency_ms)

    def add_error(self, error: str):
        """Add an error message.

        Args:
            error: Error description
        """
        self.errors.append(error)

    def calculate_percentile(self, percentile: float) -> float:
        """Calculate a specific percentile from latency data.

        Args:
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value in milliseconds
        """
        if not self.latencies:
            return 0.0

        sorted_latencies = sorted(self.latencies)
        index = int((percentile / 100) * len(sorted_latencies))
        index = min(index, len(sorted_latencies) - 1)
        return sorted_latencies[index]

    def get_summary(self) -> dict:
        """Get summary statistics of collected metrics.

        Returns:
            Dictionary with summary statistics
        """
        if not self.latencies:
            return {
                "count": 0,
                "avg_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "error_count": len(self.errors),
            }

        return {
            "count": len(self.latencies),
            "avg_latency_ms": statistics.mean(self.latencies),
            "min_latency_ms": min(self.latencies),
            "max_latency_ms": max(self.latencies),
            "p50_latency_ms": self.calculate_percentile(50),
            "p95_latency_ms": self.calculate_percentile(95),
            "p99_latency_ms": self.calculate_percentile(99),
            "error_count": len(self.errors),
        }

    def calculate_throughput(self, duration_seconds: float) -> float:
        """Calculate requests per second.

        Args:
            duration_seconds: Test duration

        Returns:
            Requests per second
        """
        if duration_seconds == 0:
            return 0.0
        return len(self.latencies) / duration_seconds

    def calculate_error_rate(self) -> float:
        """Calculate error rate percentage.

        Returns:
            Error rate (0-100)
        """
        total = len(self.latencies) + len(self.errors)
        if total == 0:
            return 0.0
        return (len(self.errors) / total) * 100

    def reset(self):
        """Reset all collected metrics."""
        self.latencies.clear()
        self.errors.clear()
        self.start_time = 0.0
        self.end_time = 0.0
