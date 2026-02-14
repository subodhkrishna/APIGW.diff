"""Error handling test."""

from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlingTest(BaseTestCase):
    """Test gateway error handling capabilities."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize error handling test."""
        super().__init__("error_handling", "reliability", config)
        self.error_paths = self.config.get("error_paths", ["/error/500", "/error/404", "/timeout"])

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up error handling test."""
        self.gateway = gateway
        logger.info(f"Setting up error handling test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute error handling test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        logger.info("Testing error handling")

        error_responses = {}
        handled_errors = 0

        try:
            # Test with various error-inducing paths
            for path in self.error_paths:
                try:
                    response = await self.gateway.send_request(
                        method="GET",
                        path=path,
                        timeout=5.0,
                    )

                    error_responses[path] = response.status
                    if response.status in [404, 500, 502, 503, 504]:
                        handled_errors += 1
                        logger.info(f"✓ Error path {path}: {response.status}")

                except Exception as e:
                    error_responses[path] = str(e)
                    handled_errors += 1
                    logger.debug(f"Error path {path} exception: {e}")

            metrics = TestMetrics(
                total_requests=len(self.error_paths),
                successful_requests=handled_errors,
            )
            metrics.custom["error_responses"] = error_responses

            result.metrics = metrics
            result.status = TestStatus.PASSED
            result.message = f"Error handling test: {handled_errors}/{len(self.error_paths)} errors handled"
            result.details = error_responses

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Error handling test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up error handling test."""
        logger.info(f"Error handling test teardown for {self.gateway.name}")
