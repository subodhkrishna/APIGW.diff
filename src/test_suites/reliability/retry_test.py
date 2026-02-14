"""Retry mechanism test."""

from typing import Optional

from ...core.gateway_interface import GatewayCapability, GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class RetryTest(BaseTestCase):
    """Test gateway retry capabilities."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize retry test."""
        config = config or {}
        config["required_capabilities"] = [GatewayCapability.RETRY.value]
        super().__init__("retry", "reliability", config)

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up retry test."""
        self.gateway = gateway
        logger.info(f"Setting up retry test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute retry test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Check if gateway supports retry
        should_skip, reason = self.should_skip(self.gateway)
        if should_skip:
            result.status = TestStatus.SKIPPED
            result.message = reason
            return result

        # Placeholder: retry testing requires specific gateway configuration
        result.status = TestStatus.SKIPPED
        result.message = "Retry test requires gateway-specific configuration"
        logger.info(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up retry test."""
        logger.info(f"Retry test teardown for {self.gateway.name}")
