"""Parallel test execution across multiple gateways."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.test_case import TestResult
from ..utils.logger import get_logger
from .test_runner import TestRunner

logger = get_logger(__name__)


class ParallelExecutor:
    """Execute tests across multiple gateways in parallel."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize parallel executor.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir

    async def run_parallel(
        self,
        gateway_names: Optional[List[str]] = None,
        test_suites: Optional[List[str]] = None,
        test_names: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> Dict[str, List[TestResult]]:
        """Run tests in parallel across all gateways.

        Args:
            gateway_names: List of gateway names to test (None = all enabled)
            test_suites: List of test suites to run (None = all enabled)
            test_names: List of specific test names to run (None = all)
            dry_run: If True, only show what would be tested

        Returns:
            Dictionary mapping gateway names to their test results
        """
        logger.info("Starting parallel test execution")

        # Load gateway configurations
        from ..utils.config_loader import ConfigLoader

        config_loader = ConfigLoader(self.config_dir)
        gateways_config = config_loader.get_enabled_gateways()

        # Filter gateways
        if gateway_names:
            gateways_config = {
                name: cfg for name, cfg in gateways_config.items() if name in gateway_names
            }

        if not gateways_config:
            logger.warning("No gateways to test")
            return {}

        # Create tasks for each gateway
        tasks = []
        gateway_list = list(gateways_config.keys())

        for gateway_name in gateway_list:
            task = self._run_gateway_tests(
                gateway_name=[gateway_name],
                test_suites=test_suites,
                test_names=test_names,
                dry_run=dry_run,
            )
            tasks.append(task)

        # Execute all tasks in parallel
        logger.info(f"Running tests for {len(gateway_list)} gateways in parallel")
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize results by gateway
        results_by_gateway = {}
        for gateway_name, result in zip(gateway_list, results_list):
            if isinstance(result, Exception):
                logger.error(f"Gateway {gateway_name} failed: {result}")
                results_by_gateway[gateway_name] = []
            else:
                results_by_gateway[gateway_name] = result

        return results_by_gateway

    async def _run_gateway_tests(
        self,
        gateway_name: List[str],
        test_suites: Optional[List[str]] = None,
        test_names: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> List[TestResult]:
        """Run tests for a single gateway.

        Args:
            gateway_name: Gateway name (as single-item list)
            test_suites: Test suites to run
            test_names: Specific tests to run
            dry_run: Dry run flag

        Returns:
            List of test results
        """
        runner = TestRunner(self.config_dir)
        return await runner.run_tests(
            gateway_names=gateway_name,
            test_suites=test_suites,
            test_names=test_names,
            dry_run=dry_run,
        )

    def get_combined_summary(
        self, results_by_gateway: Dict[str, List[TestResult]]
    ) -> Dict[str, Any]:
        """Get combined summary of all gateway results.

        Args:
            results_by_gateway: Results organized by gateway

        Returns:
            Combined summary dictionary
        """
        all_results = []
        for results in results_by_gateway.values():
            all_results.extend(results)

        from collections import Counter

        status_counts = Counter(r.status.value for r in all_results)

        gateway_summaries = {}
        for gateway_name, results in results_by_gateway.items():
            gateway_status = Counter(r.status.value for r in results)
            gateway_summaries[gateway_name] = {
                "total": len(results),
                "passed": gateway_status.get("passed", 0),
                "failed": gateway_status.get("failed", 0),
                "skipped": gateway_status.get("skipped", 0),
                "error": gateway_status.get("error", 0),
            }

        return {
            "total": len(all_results),
            "passed": status_counts.get("passed", 0),
            "failed": status_counts.get("failed", 0),
            "skipped": status_counts.get("skipped", 0),
            "error": status_counts.get("error", 0),
            "gateways": list(results_by_gateway.keys()),
            "gateway_summaries": gateway_summaries,
        }
