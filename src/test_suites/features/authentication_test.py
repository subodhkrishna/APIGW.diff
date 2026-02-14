"""Authentication feature test."""

from typing import Optional

from ...core.gateway_interface import GatewayCapability, GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationTest(BaseTestCase):
    """Test gateway authentication capabilities."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize authentication test.

        Args:
            config: Test configuration with:
                - path: Protected request path (default: /)
                - auth_header: Authentication header name (default: Authorization)
                - valid_token: Valid authentication token (optional)
                - invalid_token: Invalid token for negative testing (default: "invalid")
        """
        config = config or {}
        config["required_capabilities"] = [GatewayCapability.AUTHENTICATION.value]
        super().__init__("authentication", "features", config)
        self.path = self.config.get("path", "/")
        self.auth_header = self.config.get("auth_header", "Authorization")
        self.valid_token = self.config.get("valid_token")
        self.invalid_token = self.config.get("invalid_token", "invalid")

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up authentication test."""
        self.gateway = gateway
        logger.info(f"Setting up authentication test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute authentication test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Check if gateway supports authentication
        should_skip, reason = self.should_skip(self.gateway)
        if should_skip:
            result.status = TestStatus.SKIPPED
            result.message = reason
            return result

        logger.info("Testing authentication mechanisms")

        tests_run = 0
        tests_passed = 0

        try:
            # Test 1: Request without authentication
            try:
                response = await self.gateway.send_request(
                    method="GET",
                    path=self.path,
                    timeout=5.0,
                )
                tests_run += 1

                if response.status in [401, 403]:
                    tests_passed += 1
                    result.details["no_auth_blocked"] = True
                    logger.info("✓ Request without auth properly rejected")
                else:
                    result.details["no_auth_blocked"] = False
                    logger.warning(f"✗ Request without auth returned {response.status}")

            except Exception as e:
                logger.debug(f"No auth test error: {e}")

            # Test 2: Request with invalid authentication
            try:
                response = await self.gateway.send_request(
                    method="GET",
                    path=self.path,
                    headers={self.auth_header: self.invalid_token},
                    timeout=5.0,
                )
                tests_run += 1

                if response.status in [401, 403]:
                    tests_passed += 1
                    result.details["invalid_auth_blocked"] = True
                    logger.info("✓ Request with invalid auth properly rejected")
                else:
                    result.details["invalid_auth_blocked"] = False
                    logger.warning(f"✗ Request with invalid auth returned {response.status}")

            except Exception as e:
                logger.debug(f"Invalid auth test error: {e}")

            # Test 3: Request with valid authentication (if token provided)
            if self.valid_token:
                try:
                    response = await self.gateway.send_request(
                        method="GET",
                        path=self.path,
                        headers={self.auth_header: self.valid_token},
                        timeout=5.0,
                    )
                    tests_run += 1

                    if response.status < 400:
                        tests_passed += 1
                        result.details["valid_auth_allowed"] = True
                        logger.info("✓ Request with valid auth accepted")
                    else:
                        result.details["valid_auth_allowed"] = False
                        logger.warning(f"✗ Request with valid auth returned {response.status}")

                except Exception as e:
                    logger.debug(f"Valid auth test error: {e}")

            metrics = TestMetrics(
                total_requests=tests_run,
                successful_requests=tests_passed,
                failed_requests=tests_run - tests_passed,
            )
            metrics.custom["tests_run"] = tests_run
            metrics.custom["tests_passed"] = tests_passed

            result.metrics = metrics
            result.status = TestStatus.PASSED if tests_passed >= tests_run // 2 else TestStatus.FAILED
            result.message = f"Authentication test: {tests_passed}/{tests_run} checks passed"

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Authentication test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up authentication test."""
        logger.info(f"Authentication test teardown for {self.gateway.name}")
