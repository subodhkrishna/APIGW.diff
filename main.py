"""CLI entry point for API Gateway Comparison Testing Framework."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from src.reporters import ConsoleReporter, HTMLReporter, JSONReporter
from src.runners import ParallelExecutor, TestRunner
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

console = Console()


@click.group()
@click.option("--config-dir", type=click.Path(exists=True), help="Configuration directory")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config_dir: Optional[str], verbose: bool):
    """API Gateway Comparison Testing Framework."""
    ctx.ensure_object(dict)
    ctx.obj["config_dir"] = Path(config_dir) if config_dir else None
    ctx.obj["verbose"] = verbose

    # Setup logging
    import logging

    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logger(level=log_level)


@cli.group()
def test():
    """Test management commands."""
    pass


@test.command("run")
@click.option("--gateway", "-g", multiple=True, help="Specific gateway(s) to test")
@click.option("--suite", "-s", multiple=True, help="Specific test suite(s) to run")
@click.option("--test", "-t", multiple=True, help="Specific test(s) to run")
@click.option(
    "--parallel", "-p", is_flag=True, help="Run tests in parallel across all gateways"
)
@click.option("--output", "-o", type=click.Choice(["console", "json", "html"]), default="console")
@click.option("--report-dir", type=click.Path(), default="reports", help="Report output directory")
@click.option("--dry-run", is_flag=True, help="Show what would be tested without running")
@click.pass_context
def run_tests(
    ctx,
    gateway: tuple,
    suite: tuple,
    test: tuple,
    parallel: bool,
    output: str,
    report_dir: str,
    dry_run: bool,
):
    """Run tests against API gateways."""
    config_dir = ctx.obj["config_dir"]

    gateway_names = list(gateway) if gateway else None
    test_suites = list(suite) if suite else None
    test_names = list(test) if test else None
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    try:
        if parallel:
            console.print("[bold blue]Running tests in parallel mode[/bold blue]\n")
            results = asyncio.run(
                _run_parallel_tests(
                    config_dir, gateway_names, test_suites, test_names, dry_run
                )
            )
            summary = _get_parallel_summary(results)
            all_results = []
            for gateway_results in results.values():
                all_results.extend(gateway_results)
        else:
            console.print("[bold blue]Running tests in sequential mode[/bold blue]\n")
            all_results = asyncio.run(
                _run_sequential_tests(config_dir, gateway_names, test_suites, test_names, dry_run)
            )
            summary = _get_summary(all_results)

        if not dry_run:
            # Generate reports
            asyncio.run(_generate_reports(all_results, summary, output, report_path))

            # Print summary
            _print_summary(summary)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", err=True)
        if ctx.obj["verbose"]:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@test.command("list")
@click.pass_context
def list_tests(ctx):
    """List available tests."""
    from src.runners.test_runner import TEST_REGISTRY

    console.print("\n[bold]Available Tests:[/bold]\n")

    tests_by_category = {}
    for test_name in TEST_REGISTRY.keys():
        # Get test instance to find category
        test_class = TEST_REGISTRY[test_name]
        test = test_class()
        category = test.category

        if category not in tests_by_category:
            tests_by_category[category] = []
        tests_by_category[category].append(test_name)

    for category, tests in sorted(tests_by_category.items()):
        console.print(f"[cyan]{category.upper()}[/cyan]")
        for test_name in sorted(tests):
            console.print(f"  • {test_name}")
        console.print()


@cli.group()
def gateway():
    """Gateway management commands."""
    pass


@gateway.command("list")
@click.pass_context
def list_gateways(ctx):
    """List configured gateways."""
    config_dir = ctx.obj["config_dir"]

    try:
        config_loader = ConfigLoader(config_dir)
        gateways = config_loader.get_enabled_gateways()

        console.print("\n[bold]Configured Gateways:[/bold]\n")

        if not gateways:
            console.print("[yellow]No gateways configured or enabled[/yellow]")
            return

        for name, config in gateways.items():
            status = "[green]enabled[/green]" if config.get("enabled", True) else "[red]disabled[/red]"
            url = config.get("url") or config.get("proxy_url") or "N/A"
            console.print(f"[cyan]{name}[/cyan] ({status})")
            console.print(f"  URL: {url}")
            console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", err=True)
        sys.exit(1)


async def _run_sequential_tests(config_dir, gateway_names, test_suites, test_names, dry_run):
    """Run tests sequentially."""
    runner = TestRunner(config_dir)
    return await runner.run_tests(
        gateway_names=gateway_names,
        test_suites=test_suites,
        test_names=test_names,
        dry_run=dry_run,
    )


async def _run_parallel_tests(config_dir, gateway_names, test_suites, test_names, dry_run):
    """Run tests in parallel."""
    executor = ParallelExecutor(config_dir)
    return await executor.run_parallel(
        gateway_names=gateway_names,
        test_suites=test_suites,
        test_names=test_names,
        dry_run=dry_run,
    )


def _get_summary(results):
    """Get summary from results."""
    runner = TestRunner()
    runner.results = results
    return runner.get_summary()


def _get_parallel_summary(results_by_gateway):
    """Get summary from parallel results."""
    executor = ParallelExecutor()
    return executor.get_combined_summary(results_by_gateway)


async def _generate_reports(results, summary, output_format, report_dir):
    """Generate reports in requested format."""
    if output_format == "json":
        reporter = JSONReporter(report_dir)
        output_file = await reporter.generate(results, summary)
        console.print(f"\n[green]✓[/green] JSON report: {output_file}")

    elif output_format == "html":
        reporter = HTMLReporter(report_dir)
        output_file = await reporter.generate(results, summary)
        console.print(f"\n[green]✓[/green] HTML report: {output_file}")

    elif output_format == "console":
        reporter = ConsoleReporter(report_dir)
        await reporter.generate(results, summary)


def _print_summary(summary):
    """Print summary to console."""
    console.print("\n[bold]Test Summary:[/bold]")
    console.print(f"Total: {summary['total']}")
    console.print(f"[green]Passed: {summary['passed']}[/green]")
    console.print(f"[red]Failed: {summary['failed']}[/red]")
    console.print(f"[yellow]Skipped: {summary['skipped']}[/yellow]")
    console.print(f"[red]Errors: {summary['error']}[/red]")


if __name__ == "__main__":
    cli(obj={})
