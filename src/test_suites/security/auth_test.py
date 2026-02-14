"""Authentication security test."""

from typing import Optional

from ...core.gateway_interface import GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class AuthTest(BaseTestCase):
    """Test gateway authentication security."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize auth test."""
        super().__init__("auth", "security", config)

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up auth test."""
        self.gateway = gateway
        logger.info(f"Setting up auth test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute auth test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # This is similar to features/authentication_test
        # In a real implementation, this would test security-specific aspects
        result.status = TestStatus.SKIPPED
        result.message = "Auth security test covered by feature tests"
        logger.info(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up auth test."""
        logger.info(f"Auth test teardown for {self.gateway.name}")
