"""TLS/SSL configuration test."""

from typing import Optional

from ...core.gateway_interface import GatewayCapability, GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class TLSTest(BaseTestCase):
    """Test gateway TLS/SSL configuration."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize TLS test."""
        config = config or {}
        config["required_capabilities"] = [GatewayCapability.TLS_TERMINATION.value]
        super().__init__("tls", "security", config)

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up TLS test."""
        self.gateway = gateway
        logger.info(f"Setting up TLS test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute TLS test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Check if gateway supports TLS
        should_skip, reason = self.should_skip(self.gateway)
        if should_skip:
            result.status = TestStatus.SKIPPED
            result.message = reason
            return result

        logger.info("Testing TLS configuration")

        try:
            # Check if gateway URL uses HTTPS
            if self.gateway.base_url.startswith("https://"):
                result.status = TestStatus.PASSED
                result.message = "Gateway uses HTTPS"
                result.details["tls_enabled"] = True
            else:
                result.status = TestStatus.FAILED
                result.message = "Gateway does not use HTTPS"
                result.details["tls_enabled"] = False

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"TLS test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up TLS test."""
        logger.info(f"TLS test teardown for {self.gateway.name}")
