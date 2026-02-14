"""Load testing with gradual ramp-up."""

import asyncio
import time
from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger
from ...utils.metrics import MetricsCollector

logger = get_logger(__name__)


class LoadTest(BaseTestCase):
    """Load test with gradual ramp-up of concurrent requests."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize load test.

        Args:
            config: Test configuration with:
                - max_concurrent: Maximum concurrent requests (default: 50)
                - ramp_up_time: Ramp-up duration in seconds (default: 10)
                - sustained_time: Sustained load duration in seconds (default: 20)
                - path: Request path (default: /)
        """
        super().__init__("load", "performance", config)
        self.max_concurrent = self.config.get("max_concurrent", 50)
        self.ramp_up_time = self.config.get("ramp_up_time", 10)
        self.sustained_time = self.config.get("sustained_time", 20)
        self.path = self.config.get("path", "/")
        self.metrics_collector = MetricsCollector()
        self._stop = False

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up load test."""
        self.gateway = gateway
        logger.info(f"Setting up load test for {gateway.name}")

    async def _worker(self, worker_id: int):
        """Worker coroutine."""
        while not self._stop:
            try:
                request_start = time.perf_counter()
                response = await self.gateway.send_request(
                    method="GET",
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

            await asyncio.sleep(0.01)

    async def execute(self) -> TestResult:
        """Execute load test with ramp-up."""
        logger.info(
            f"Running load test: ramp to {self.max_concurrent} over {self.ramp_up_time}s, "
            f"sustain for {self.sustained_time}s"
        )

        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        self._stop = False
        workers = []

        try:
            start_time = time.perf_counter()

            # Ramp-up phase: gradually add workers
            step_time = self.ramp_up_time / self.max_concurrent
            for i in range(self.max_concurrent):
                workers.append(asyncio.create_task(self._worker(i)))
                await asyncio.sleep(step_time)

            # Sustained load phase
            await asyncio.sleep(self.sustained_time)

            # Stop all workers
            self._stop = True
            await asyncio.gather(*workers, return_exceptions=True)

            end_time = time.perf_counter()
            total_duration = end_time - start_time

            # Calculate metrics
            summary = self.metrics_collector.get_summary()
            total_requests = summary["count"] + summary["error_count"]

            metrics = TestMetrics(
                duration_seconds=total_duration,
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
                requests_per_second=self.metrics_collector.calculate_throughput(total_duration),
            )

            metrics.custom["max_concurrent"] = self.max_concurrent
            metrics.custom["ramp_up_time"] = self.ramp_up_time
            metrics.custom["sustained_time"] = self.sustained_time

            result.metrics = metrics
            result.status = (
                TestStatus.PASSED if metrics.successful_requests > 0 else TestStatus.FAILED
            )
            result.message = (
                f"Load test completed: {total_requests} requests, "
                f"{metrics.requests_per_second:.2f} req/s, "
                f"error rate: {metrics.error_rate:.2f}%"
            )

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Load test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up load test."""
        self._stop = True
        logger.info(f"Load test teardown for {self.gateway.name}")
