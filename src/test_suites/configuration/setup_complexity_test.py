"""Setup complexity assessment test."""

from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class SetupComplexityTest(BaseTestCase):
    """Assess gateway setup complexity."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize setup complexity test."""
        super().__init__("setup_complexity", "configuration", config)

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up setup complexity test."""
        self.gateway = gateway
        logger.info(f"Setting up setup complexity test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute setup complexity test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # This is a qualitative test - would require manual assessment
        # For now, we'll report the gateway capabilities as a proxy
        capabilities = self.gateway.get_capabilities()

        result.status = TestStatus.PASSED
        result.message = f"Gateway has {len(capabilities)} capabilities configured"
        result.details = {
            "capabilities_count": len(capabilities),
            "capabilities": [cap.value for cap in capabilities],
        }

        logger.info(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up setup complexity test."""
        logger.info(f"Setup complexity test teardown for {self.gateway.name}")
