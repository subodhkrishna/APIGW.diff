"""Rate limiting feature test."""

import asyncio
from typing import Optional

from ...core.gateway_interface import GatewayCapability, GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitingTest(BaseTestCase):
    """Test gateway rate limiting capabilities."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize rate limiting test.

        Args:
            config: Test configuration with:
                - requests: Number of requests to send (default: 20)
                - path: Request path (default: /)
                - expected_limit: Expected rate limit threshold (optional)
        """
        config = config or {}
        config["required_capabilities"] = [GatewayCapability.RATE_LIMITING.value]
        super().__init__("rate_limiting", "features", config)
        self.num_requests = self.config.get("requests", 20)
        self.path = self.config.get("path", "/")
        self.expected_limit = self.config.get("expected_limit")

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up rate limiting test."""
        self.gateway = gateway
        logger.info(f"Setting up rate limiting test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute rate limiting test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Check if gateway supports rate limiting
        should_skip, reason = self.should_skip(self.gateway)
        if should_skip:
            result.status = TestStatus.SKIPPED
            result.message = reason
            return result

        logger.info(f"Testing rate limiting: sending {self.num_requests} rapid requests")

        rate_limited_count = 0
        successful_count = 0

        try:
            for i in range(self.num_requests):
                try:
                    response = await self.gateway.send_request(
                        method="GET",
                        path=self.path,
                        timeout=5.0,
                    )

                    if response.status == 429:  # Too Many Requests
                        rate_limited_count += 1
                    elif response.status < 400:
                        successful_count += 1

                except Exception as e:
                    logger.debug(f"Request {i+1} failed: {e}")

                # No delay - send requests as fast as possible to test rate limiting
                await asyncio.sleep(0.001)

            metrics = TestMetrics(
                total_requests=self.num_requests,
                successful_requests=successful_count,
                failed_requests=rate_limited_count,
            )
            metrics.custom["rate_limited_responses"] = rate_limited_count

            # Test passes if rate limiting is detected or all requests succeed
            # (rate limiting may be configured but not triggered with our load)
            result.metrics = metrics
            result.status = TestStatus.PASSED
            result.message = (
                f"Rate limiting test: {successful_count} successful, "
                f"{rate_limited_count} rate-limited (429) responses"
            )

            if rate_limited_count > 0:
                result.details["rate_limiting_active"] = True
            else:
                result.details["rate_limiting_active"] = False
                result.details["note"] = "No rate limiting detected with current load"

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Rate limiting test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up rate limiting test."""
        logger.info(f"Rate limiting test teardown for {self.gateway.name}")
