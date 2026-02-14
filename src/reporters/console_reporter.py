"""Console format reporter with rich formatting."""

from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..core.test_case import TestResult, TestStatus
from ..utils.logger import get_logger
from .base_reporter import BaseReporter

logger = get_logger(__name__)


class ConsoleReporter(BaseReporter):
    """Generate formatted console output using Rich library."""

    def __init__(self, output_dir: Path):
        """Initialize console reporter."""
        super().__init__(output_dir)
        self.console = Console()

    async def generate(
        self, results: List[TestResult], summary: Dict[str, Any], output_file: str = ""
    ) -> Path:
        """Generate console report.

        Args:
            results: Test results
            summary: Summary data
            output_file: Not used for console output

        Returns:
            Path to output directory
        """
        logger.info("Generating console report")

        self.console.print("\n")
        self._print_summary(summary)
        self.console.print("\n")
        self._print_results_by_gateway(results)
        self.console.print("\n")
        self._print_performance_metrics(results)

        return self.output_dir

    def _print_summary(self, summary: Dict[str, Any]):
        """Print summary panel."""
        summary_text = f"""
[bold]Total Tests:[/bold] {summary['total']}
[bold green]Passed:[/bold green] {summary['passed']}
[bold red]Failed:[/bold red] {summary['failed']}
[bold yellow]Skipped:[/bold yellow] {summary['skipped']}
[bold red]Errors:[/bold red] {summary['error']}

[bold]Gateways:[/bold] {', '.join(summary.get('gateways', []))}
        """.strip()

        self.console.print(Panel(summary_text, title="Test Summary", border_style="blue"))

    def _print_results_by_gateway(self, results: List[TestResult]):
        """Print results organized by gateway."""
        by_gateway = self._organize_results_by_gateway(results)

        for gateway_name, gateway_results in by_gateway.items():
            table = Table(title=f"Gateway: {gateway_name}", show_header=True, header_style="bold")

            table.add_column("Test", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Duration", justify="right")
            table.add_column("Message", style="dim")

            for result in gateway_results:
                status_style = self._get_status_style(result.status)
                status_text = Text(result.status.value.upper(), style=status_style)

                table.add_row(
                    result.test_name,
                    status_text,
                    f"{result.duration_seconds():.2f}s",
                    result.message[:50] + "..." if len(result.message) > 50 else result.message,
                )

            self.console.print(table)
            self.console.print()

    def _print_performance_metrics(self, results: List[TestResult]):
        """Print performance metrics table."""
        # Filter results with performance metrics
        perf_results = [
            r
            for r in results
            if r.metrics.avg_latency_ms is not None and r.status == TestStatus.PASSED
        ]

        if not perf_results:
            return

        table = Table(title="Performance Metrics", show_header=True, header_style="bold")

        table.add_column("Gateway", style="cyan")
        table.add_column("Test", style="cyan")
        table.add_column("Avg Latency", justify="right")
        table.add_column("P95 Latency", justify="right")
        table.add_column("Throughput", justify="right")
        table.add_column("Success Rate", justify="right")

        for result in perf_results:
            m = result.metrics
            table.add_row(
                result.gateway_name,
                result.test_name,
                f"{m.avg_latency_ms:.2f}ms" if m.avg_latency_ms else "N/A",
                f"{m.p95_latency_ms:.2f}ms" if m.p95_latency_ms else "N/A",
                f"{m.requests_per_second:.2f} req/s" if m.requests_per_second else "N/A",
                f"{m.success_rate():.1f}%",
            )

        self.console.print(table)

    def _get_status_style(self, status: TestStatus) -> str:
        """Get Rich style for status."""
        return {
            TestStatus.PASSED: "bold green",
            TestStatus.FAILED: "bold red",
            TestStatus.SKIPPED: "bold yellow",
            TestStatus.ERROR: "bold red",
            TestStatus.RUNNING: "bold blue",
            TestStatus.PENDING: "dim",
        }.get(status, "")
