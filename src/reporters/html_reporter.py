"""HTML format reporter with charts."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Template

from ..core.test_case import TestResult, TestStatus
from ..utils.logger import get_logger
from .base_reporter import BaseReporter

logger = get_logger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Gateway Comparison Test Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .summary-card {
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .summary-card.total { background-color: #e3f2fd; }
        .summary-card.passed { background-color: #e8f5e9; }
        .summary-card.failed { background-color: #ffebee; }
        .summary-card.skipped { background-color: #fff3e0; }
        .summary-card.error { background-color: #fce4ec; }
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 2em;
            color: #333;
        }
        .summary-card p {
            margin: 0;
            color: #666;
            font-size: 0.9em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status.passed { background-color: #4caf50; color: white; }
        .status.failed { background-color: #f44336; color: white; }
        .status.skipped { background-color: #ff9800; color: white; }
        .status.error { background-color: #e91e63; color: white; }
        .gateway-section {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }
        .gateway-section h3 {
            margin-top: 0;
            color: #007bff;
        }
        .timestamp {
            color: #999;
            font-size: 0.9em;
        }
        .metric-value {
            font-weight: 600;
            color: #007bff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>API Gateway Comparison Test Results</h1>
        <p class="timestamp">Generated: {{ generated_at }}</p>

        <h2>Summary</h2>
        <div class="summary">
            <div class="summary-card total">
                <h3>{{ summary.total }}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>{{ summary.passed }}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>{{ summary.failed }}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card skipped">
                <h3>{{ summary.skipped }}</h3>
                <p>Skipped</p>
            </div>
            <div class="summary-card error">
                <h3>{{ summary.error }}</h3>
                <p>Errors</p>
            </div>
        </div>

        <h2>Results by Gateway</h2>
        {% for gateway_name, gateway_results in results_by_gateway.items() %}
        <div class="gateway-section">
            <h3>{{ gateway_name }}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Test</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Avg Latency</th>
                        <th>P95 Latency</th>
                        <th>Success Rate</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in gateway_results %}
                    <tr>
                        <td>{{ result.test_name }}</td>
                        <td><span class="status {{ result.status }}">{{ result.status|upper }}</span></td>
                        <td>{{ "%.2f"|format(result.duration_seconds) }}s</td>
                        <td>{{ "%.2f ms"|format(result.metrics.avg_latency_ms) if result.metrics.avg_latency_ms else "N/A" }}</td>
                        <td>{{ "%.2f ms"|format(result.metrics.p95_latency_ms) if result.metrics.p95_latency_ms else "N/A" }}</td>
                        <td>{{ "%.1f%%"|format(result.metrics.success_rate) if result.metrics.total_requests > 0 else "N/A" }}</td>
                        <td>{{ result.message }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}

        <h2>Performance Comparison</h2>
        <table>
            <thead>
                <tr>
                    <th>Gateway</th>
                    <th>Test</th>
                    <th>Avg Latency</th>
                    <th>P95 Latency</th>
                    <th>P99 Latency</th>
                    <th>Throughput</th>
                </tr>
            </thead>
            <tbody>
                {% for result in perf_results %}
                <tr>
                    <td>{{ result.gateway_name }}</td>
                    <td>{{ result.test_name }}</td>
                    <td class="metric-value">{{ "%.2f ms"|format(result.metrics.avg_latency_ms) }}</td>
                    <td class="metric-value">{{ "%.2f ms"|format(result.metrics.p95_latency_ms) }}</td>
                    <td class="metric-value">{{ "%.2f ms"|format(result.metrics.p99_latency_ms) if result.metrics.p99_latency_ms else "N/A" }}</td>
                    <td class="metric-value">{{ "%.2f req/s"|format(result.metrics.requests_per_second) if result.metrics.requests_per_second else "N/A" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


class HTMLReporter(BaseReporter):
    """Generate HTML format test reports."""

    async def generate(
        self, results: List[TestResult], summary: Dict[str, Any], output_file: str = "results.html"
    ) -> Path:
        """Generate HTML report.

        Args:
            results: Test results
            summary: Summary data
            output_file: Output filename

        Returns:
            Path to generated HTML file
        """
        logger.info("Generating HTML report")

        output_path = self.output_dir / output_file

        # Organize results
        results_by_gateway = {}
        for gateway_name, gateway_results in self._organize_results_by_gateway(results).items():
            results_by_gateway[gateway_name] = [self._result_to_dict(r) for r in gateway_results]

        # Get performance results
        perf_results = [
            self._result_to_dict(r)
            for r in results
            if r.metrics.avg_latency_ms is not None and r.status == TestStatus.PASSED
        ]

        # Render template
        template = Template(HTML_TEMPLATE)
        html_content = template.render(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            results_by_gateway=results_by_gateway,
            perf_results=perf_results,
        )

        with open(output_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to: {output_path}")
        return output_path

    def _result_to_dict(self, result: TestResult) -> Dict[str, Any]:
        """Convert result to dictionary for template."""
        return {
            "test_name": result.test_name,
            "gateway_name": result.gateway_name,
            "status": result.status.value,
            "message": result.message,
            "duration_seconds": result.duration_seconds(),
            "metrics": {
                "avg_latency_ms": result.metrics.avg_latency_ms,
                "p50_latency_ms": result.metrics.p50_latency_ms,
                "p95_latency_ms": result.metrics.p95_latency_ms,
                "p99_latency_ms": result.metrics.p99_latency_ms,
                "requests_per_second": result.metrics.requests_per_second,
                "total_requests": result.metrics.total_requests,
                "success_rate": result.metrics.success_rate(),
            },
        }
