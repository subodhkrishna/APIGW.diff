"""JSON format reporter."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..core.test_case import TestResult
from ..utils.logger import get_logger
from .base_reporter import BaseReporter

logger = get_logger(__name__)


class JSONReporter(BaseReporter):
    """Generate JSON format test reports."""

    async def generate(
        self, results: List[TestResult], summary: Dict[str, Any], output_file: str = "results.json"
    ) -> Path:
        """Generate JSON report.

        Args:
            results: Test results
            summary: Summary data
            output_file: Output filename

        Returns:
            Path to generated JSON file
        """
        logger.info("Generating JSON report")

        output_path = self.output_dir / output_file

        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "results": [result.to_dict() for result in results],
            "results_by_gateway": self._organize_by_gateway(results),
            "results_by_test": self._organize_by_test(results),
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"JSON report saved to: {output_path}")
        return output_path

    def _organize_by_gateway(self, results: List[TestResult]) -> Dict[str, Any]:
        """Organize results by gateway."""
        by_gateway = self._organize_results_by_gateway(results)
        return {
            gateway: [result.to_dict() for result in gateway_results]
            for gateway, gateway_results in by_gateway.items()
        }

    def _organize_by_test(self, results: List[TestResult]) -> Dict[str, Any]:
        """Organize results by test."""
        by_test = self._organize_results_by_test(results)
        return {
            test: [result.to_dict() for result in test_results]
            for test, test_results in by_test.items()
        }
