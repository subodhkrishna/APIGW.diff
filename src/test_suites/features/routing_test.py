"""Routing feature test."""

from typing import List, Optional

from ...core.gateway_interface import GatewayCapability, GatewayInterface
from ...core.test_case import BaseTestCase, TestResult, TestMetrics, TestStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class RoutingTest(BaseTestCase):
    """Test gateway routing capabilities."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize routing test.

        Args:
            config: Test configuration with:
                - paths: List of paths to test (default: ["/", "/api/v1", "/health"])
        """
        config = config or {}
        config["required_capabilities"] = [GatewayCapability.ROUTING.value]
        super().__init__("routing", "features", config)
        self.paths = self.config.get("paths", ["/", "/api/v1", "/health"])

    async def setup(self, gateway: GatewayInterface) -> None:
        """Set up routing test."""
        self.gateway = gateway
        logger.info(f"Setting up routing test for {gateway.name}")

    async def execute(self) -> TestResult:
        """Execute routing test."""
        result = TestResult(
            test_name=self.name,
            gateway_name=self.gateway.name,
            status=TestStatus.RUNNING,
        )

        # Check if gateway supports routing
        should_skip, reason = self.should_skip(self.gateway)
        if should_skip:
            result.status = TestStatus.SKIPPED
            result.message = reason
            return result

        logger.info(f"Testing routing: checking {len(self.paths)} paths")

        successful_routes = 0
        failed_routes = 0
        route_results = {}

        try:
            for path in self.paths:
                try:
                    response = await self.gateway.send_request(
                        method="GET",
                        path=path,
                        timeout=5.0,
                    )

                    # Consider 2xx, 3xx, and 404 as successful routing
                    # (404 means route works but endpoint not configured)
                    if response.status < 500:
                        successful_routes += 1
                        route_results[path] = {"status": response.status, "routed": True}
                        logger.info(f"✓ Route {path}: {response.status}")
                    else:
                        failed_routes += 1
                        route_results[path] = {"status": response.status, "routed": False}
                        logger.warning(f"✗ Route {path}: {response.status}")

                except Exception as e:
                    failed_routes += 1
                    route_results[path] = {"error": str(e), "routed": False}
                    logger.debug(f"Route {path} failed: {e}")

            metrics = TestMetrics(
                total_requests=len(self.paths),
                successful_requests=successful_routes,
                failed_requests=failed_routes,
            )
            metrics.custom["route_results"] = route_results

            result.metrics = metrics
            result.status = TestStatus.PASSED if successful_routes > 0 else TestStatus.FAILED
            result.message = (
                f"Routing test: {successful_routes}/{len(self.paths)} routes accessible"
            )
            result.details = route_results

            logger.info(result.message)

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Routing test failed: {str(e)}"
            logger.error(result.message)

        return result

    async def teardown(self) -> None:
        """Clean up routing test."""
        logger.info(f"Routing test teardown for {self.gateway.name}")
