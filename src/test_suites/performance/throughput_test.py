"""Throughput measurement test."""

import asyncio
import time
from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger
from ...utils.metrics import MetricsCollector

logger = get_logger(__name__)


class ThroughputTest(BaseTestCase):
    """Measure gateway throughput with concurrent requests."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize throughput test.

        Args:
            config: Test configuration with:
                - duration: Test duration in seconds (default: 30)
                - concurrent: Number of concurrent requests (default: 10)
                - path: Request path (default: /)
                - method: HTTP method (default: GET)
        """
        super().__init__("throughput", "performance", config)
        self.duration = self.config.get("duration", 30)
        self.concurrent = self.config.get("concurrent", 10)
        self.path = self.config.get("path", "/")
        self.method = self.config.get("method", "GET")
        self.metrics_collector = MetricsCollector()
        self._stop = False

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up throughput test."""
        self.gateway = gateway
        logger.info(f"Setting up throughput test for {gateway.name}")

    async def _worker(self, worker_id: int):
        """Worker coroutine that sends requests continuously."""
        while not self._stop:
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
                else:
                    self.metrics_collector.add_error(f"HTTP {response.status}")

            except Exception as e:
                self.metrics_collector.add_error(str(e))
                logger.debug(f"Worker {worker_id} request failed: {e}")

            # Tiny delay to prevent tight loop
            await asyncio.sleep(0.001)

    async def execute(self) -> TestResult:
        """Execute throughput test."""
        logger.info(
            f"Running throughput test: {self.concurrent} concurrent requests for {self.duration}s"
        )

        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        self._stop = False

        try:
            # Start worker tasks
            workers = [asyncio.create_task(self._worker(i)) for i in range(self.concurrent)]

            # Run for specified duration
            await asyncio.sleep(self.duration)

            # Stop workers
            self._stop = True
            await asyncio.gather(*workers, return_exceptions=True)

            # Calculate metrics
            summary = self.metrics_collector.get_summary()
            total_requests = summary["count"] + summary["error_count"]

            metrics = TestMetrics(
                duration_seconds=self.duration,
                avg_latency_ms=summary["avg_latency_ms"],
                p50_latency_ms=summary["p50_latency_ms"],
                p95_latency_ms=summary["p95_latency_ms"],
                p99_latency_ms=summary["p99_latency_ms"],
                max_latency_ms=summary["max_latency_ms"],
                min_latency_ms=summary["min_latency_ms"],
                total_requests=total_requests,
                successful_requests=summary["count"],
                failed_requests=summary["error_count"],
                error_rate=self.metrics_collector.calculate_error_rate(),
                requests_per_second=self.metrics_collector.calculate_throughput(self.duration),
            )

            result.metrics = metrics
            result.status = (
                TestStatus.PASSED if metrics.successful_requests > 0 else TestStatus.FAILED
            )
            result.message = (
                f"Completed {total_requests} requests in {self.duration}s. "
                f"Throughput: {metrics.requests_per_second:.2f} req/s, "
                f"Avg latency: {summary['avg_latency_ms']:.2f}ms"
            )

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Throughput test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up throughput test."""
        self._stop = True
        logger.info(f"Throughput test teardown for {self.gateway.name}")
