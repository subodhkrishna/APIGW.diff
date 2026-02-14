"""CORS policy test."""

from typing import Optional

from ...core.gateway_interface import GatewayCapability, GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class CORSTest(BaseTestCase):
    """Test gateway CORS policy."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize CORS test."""
        config = config or {}
        config["required_capabilities"] = [GatewayCapability.CORS.value]
        super().__init__("cors", "security", config)
        self.path = self.config.get("path", "/")

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up CORS test."""
        self.gateway = gateway
        logger.info(f"Setting up CORS test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute CORS test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Check if gateway supports CORS
        should_skip, reason = self.should_skip(self.gateway)
        if should_skip:
            result.status = TestStatus.SKIPPED
            result.message = reason
            return result

        logger.info("Testing CORS policy")

        try:
            # Send OPTIONS request (CORS preflight)
            response = await self.gateway.send_request(
                method="OPTIONS",
                path=self.path,
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET",
                },
                timeout=5.0,
            )

            cors_headers = {
                "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
                "access-control-allow-methods": response.headers.get(
                    "Access-Control-Allow-Methods"
                ),
                "access-control-allow-headers": response.headers.get(
                    "Access-Control-Allow-Headers"
                ),
            }

            has_cors = any(v is not None for v in cors_headers.values())

            metrics = TestMetrics(total_requests=1, successful_requests=1 if has_cors else 0)

            result.metrics = metrics
            result.details = {"cors_headers": cors_headers, "cors_enabled": has_cors}

            if has_cors:
                result.status = TestStatus.PASSED
                result.message = "CORS headers detected"
            else:
                result.status = TestStatus.FAILED
                result.message = "No CORS headers found"

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"CORS test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up CORS test."""
        logger.info(f"CORS test teardown for {self.gateway.name}")
