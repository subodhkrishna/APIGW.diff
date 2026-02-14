"""Latency measurement test."""

import asyncio
import time
from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger
from ...utils.metrics import MetricsCollector

logger = get_logger(__name__)


class LatencyTest(BaseTestCase):
    """Measure gateway latency with percentile breakdowns."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize latency test.

        Args:
            config: Test configuration with:
                - requests: Number of requests to send (default: 100)
                - path: Request path (default: /)
                - method: HTTP method (default: GET)
        """
        super().__init__("latency", "performance", config)
        self.num_requests = self.config.get("requests", 100)
        self.path = self.config.get("path", "/")
        self.method = self.config.get("method", "GET")
        self.metrics_collector = MetricsCollector()

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up latency test."""
        self.gateway = gateway
        logger.info(f"Setting up latency test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute latency test."""
        logger.info(f"Running latency test: {self.num_requests} requests to {self.path}")

        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        start_time = time.perf_counter()
        successful_requests = 0
        failed_requests = 0

        try:
            for i in range(self.num_requests):
                try:
                    request_start = time.perf_counter()
                    response = await self.gateway.send_request(
                        method=self.method,
                        path=self.path,
                        timeout=10.0,
                    )
                    latency_ms = (time.perf_counter() - request_start) * 1000

                    if response.status < 500:
                        self.metrics_collector.add_latency(latency_ms)
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        self.metrics_collector.add_error(f"HTTP {response.status}")

                except Exception as e:
                    failed_requests += 1
                    self.metrics_collector.add_error(str(e))
                    logger.debug(f"Request {i+1} failed: {e}")

                # Small delay to avoid overwhelming the gateway
                if i < self.num_requests - 1:
                    await asyncio.sleep(0.01)

            end_time = time.perf_counter()
            duration = end_time - start_time

            # Calculate metrics
            summary = self.metrics_collector.get_summary()

            metrics = TestMetrics(
                duration_seconds=duration,
                avg_latency_ms=summary["avg_latency_ms"],
                p50_latency_ms=summary["p50_latency_ms"],
                p95_latency_ms=summary["p95_latency_ms"],
                p99_latency_ms=summary["p99_latency_ms"],
                max_latency_ms=summary["max_latency_ms"],
                min_latency_ms=summary["min_latency_ms"],
                total_requests=self.num_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                error_rate=self.metrics_collector.calculate_error_rate(),
                requests_per_second=self.metrics_collector.calculate_throughput(duration),
            )

            result.metrics = metrics
            result.status = TestStatus.PASSED if successful_requests > 0 else TestStatus.FAILED
            result.message = (
                f"Completed {successful_requests}/{self.num_requests} requests. "
                f"Avg latency: {summary['avg_latency_ms']:.2f}ms, "
                f"P95: {summary['p95_latency_ms']:.2f}ms"
            )

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Latency test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up latency test."""
        logger.info(f"Latency test teardown for {self.gateway.name}")
