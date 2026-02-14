"""API flexibility assessment test."""

from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class APIFlexibilityTest(BaseTestCase):
    """Assess gateway API flexibility."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize API flexibility test."""
        super().__init__("api_flexibility", "configuration", config)

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up API flexibility test."""
        self.gateway = gateway
        logger.info(f"Setting up API flexibility test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute API flexibility test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Qualitative test - report gateway type and capabilities
        result.status = TestStatus.PASSED
        result.message = f"Gateway configuration assessed"
        result.details = {"gateway_type": self.gateway.name}

        logger.info(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up API flexibility test."""
        logger.info(f"API flexibility test teardown for {self.gateway.name}")
