"""Main test execution engine."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..core.gateway_interface import GatewayInterface
from ..core.test_case import BaseTestCase, TestResult
from ..gateways import get_gateway_class
from ..test_suites import (
    LatencyTest, ThroughputTest, LoadTest,
    RateLimitingTest, AuthenticationTest, RoutingTest, TransformationTest,
    ErrorHandlingTest, RetryTest, CircuitBreakerTest,
    TLSTest, CORSTest, AuthTest,
    SetupComplexityTest, APIFlexibilityTest
)
from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Test registry - maps test names to test classes
TEST_REGISTRY: Dict[str, Type[BaseTestCase]] = {
    "latency": LatencyTest,
    "throughput": ThroughputTest,
    "load": LoadTest,
    "rate_limiting": RateLimitingTest,
    "authentication": AuthenticationTest,
    "routing": RoutingTest,
    "transformation": TransformationTest,
    "error_handling": ErrorHandlingTest,
    "retry": RetryTest,
    "circuit_breaker": CircuitBreakerTest,
    "tls": TLSTest,
    "auth": AuthTest,
    "cors": CORSTest,
    "setup_complexity": SetupComplexityTest,
    "api_flexibility": APIFlexibilityTest,
}


class TestRunner:
    """Main test execution engine."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize test runner.

        Args:
            config_dir: Configuration directory path
        """
        self.config_loader = ConfigLoader(config_dir)
        self.results: List[TestResult] = []

    async def run_tests(
        self,
        gateway_names: Optional[List[str]] = None,
        test_suites: Optional[List[str]] = None,
        test_names: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> List[TestResult]:
        """Run tests against specified gateways.

        Args:
            gateway_names: List of gateway names to test (None = all enabled)
            test_suites: List of test suites to run (None = all enabled)
            test_names: List of specific test names to run (None = all)
            dry_run: If True, only show what would be tested

        Returns:
            List of TestResult objects
        """
        logger.info("Starting test execution")

        # Load configurations
        gateways_config = self.config_loader.get_enabled_gateways()
        test_suites_config = self.config_loader.get_enabled_test_suites()

        # Filter gateways
        if gateway_names:
            gateways_config = {
                name: cfg for name, cfg in gateways_config.items() if name in gateway_names
            }

        # Filter test suites
        if test_suites:
            test_suites_config = {
                name: cfg for name, cfg in test_suites_config.items() if name in test_suites
            }

        # Build test list
        tests_to_run = self._build_test_list(test_suites_config, test_names)

        if not gateways_config:
            logger.warning("No gateways configured or enabled")
            return []

        if not tests_to_run:
            logger.warning("No tests to run")
            return []

        logger.info(f"Gateways to test: {', '.join(gateways_config.keys())}")
        logger.info(f"Tests to run: {', '.join([t['name'] for t in tests_to_run])}")

        if dry_run:
            logger.info("Dry run - no tests executed")
            return []

        # Execute tests for each gateway
        results = []
        for gateway_name, gateway_config in gateways_config.items():
            logger.info(f"\nTesting gateway: {gateway_name}")

            gateway_results = await self._run_tests_for_gateway(
                gateway_name, gateway_config, tests_to_run
            )
            results.extend(gateway_results)

        self.results = results
        return results

    def _build_test_list(
        self, test_suites_config: Dict[str, Any], test_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Build list of tests to run.

        Args:
            test_suites_config: Test suite configuration
            test_names: Optional specific test names to run

        Returns:
            List of test configurations
        """
        tests = []

        for suite_name, suite_config in test_suites_config.items():
            suite_tests = suite_config.get("tests", [])
            suite_config_data = suite_config.get("config", {})

            for test_name in suite_tests:
                # Skip if specific tests requested and this isn't one of them
                if test_names and test_name not in test_names:
                    continue

                if test_name in TEST_REGISTRY:
                    tests.append(
                        {
                            "name": test_name,
                            "class": TEST_REGISTRY[test_name],
                            "config": suite_config_data,
                            "suite": suite_name,
                        }
                    )

        return tests

    async def _run_tests_for_gateway(
        self, gateway_name: str, gateway_config: Dict[str, Any], tests: List[Dict[str, Any]]
    ) -> List[TestResult]:
        """Run all tests for a specific gateway.

        Args:
            gateway_name: Gateway name
            gateway_config: Gateway configuration
            tests: List of tests to run

        Returns:
            List of test results
        """
        results = []

        try:
            # Create and configure gateway
            gateway_class = get_gateway_class(gateway_name)
            gateway = gateway_class(gateway_name, gateway_config)

            async with gateway:
                # Health check
                healthy = await gateway.health_check()
                if not healthy:
                    logger.warning(f"Gateway {gateway_name} health check failed")
                else:
                    logger.info(f"Gateway {gateway_name} is healthy")

                # Run tests
                for test_info in tests:
                    test_class = test_info["class"]
                    test_config = test_info["config"]

                    logger.info(f"Running test: {test_info['name']}")

                    try:
                        test = test_class(test_config)
                        result = await test.run(gateway)
                        results.append(result)

                        status_symbol = {
                            "passed": "✓",
                            "failed": "✗",
                            "skipped": "○",
                            "error": "✗",
                        }.get(result.status.value, "?")

                        logger.info(f"{status_symbol} {test_info['name']}: {result.message}")

                    except Exception as e:
                        logger.error(f"Test {test_info['name']} crashed: {e}")

        except Exception as e:
            logger.error(f"Failed to run tests for {gateway_name}: {e}")

        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of test results.

        Returns:
            Summary dictionary
        """
        if not self.results:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "error": 0}

        from collections import Counter

        status_counts = Counter(r.status.value for r in self.results)

        return {
            "total": len(self.results),
            "passed": status_counts.get("passed", 0),
            "failed": status_counts.get("failed", 0),
            "skipped": status_counts.get("skipped", 0),
            "error": status_counts.get("error", 0),
            "gateways": list(set(r.gateway_name for r in self.results)),
            "tests": list(set(r.test_name for r in self.results)),
        }
