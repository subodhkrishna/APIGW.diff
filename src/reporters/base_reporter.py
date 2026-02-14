"""Base reporter interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from ..core.test_case import TestResult


class BaseReporter(ABC):
    """Abstract base class for result reporters."""

    def __init__(self, output_dir: Path):
        """Initialize reporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def generate(
        self, results: List[TestResult], summary: Dict[str, Any], output_file: str
    ) -> Path:
        """Generate report from test results.

        Args:
            results: List of test results
            summary: Summary dictionary
            output_file: Output filename

        Returns:
            Path to generated report file
        """
        pass

    def _organize_results_by_gateway(
        self, results: List[TestResult]
    ) -> Dict[str, List[TestResult]]:
        """Organize results by gateway name.

        Args:
            results: List of test results

        Returns:
            Dictionary mapping gateway names to their results
        """
        by_gateway = {}
        for result in results:
            if result.gateway_name not in by_gateway:
                by_gateway[result.gateway_name] = []
            by_gateway[result.gateway_name].append(result)
        return by_gateway

    def _organize_results_by_test(self, results: List[TestResult]) -> Dict[str, List[TestResult]]:
        """Organize results by test name.

        Args:
            results: List of test results

        Returns:
            Dictionary mapping test names to their results
        """
        by_test = {}
        for result in results:
            if result.test_name not in by_test:
                by_test[result.test_name] = []
            by_test[result.test_name].append(result)
        return by_test
