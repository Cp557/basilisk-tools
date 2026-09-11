"""Command-line entry point for Basilisk Tools."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from basilisk_tools import __version__
from basilisk_tools.doctor import collect_doctor_report
from basilisk_tools.inspection import (
    DEFAULT_INSPECTION_TIMEOUT_SECONDS,
    inspect_scenario,
)
from basilisk_tools.results import RunResult, RunStatus
from basilisk_tools.runner import (
    DEFAULT_RUNS_DIRECTORY,
    DEFAULT_TIMEOUT_SECONDS,
    run_scenario,
)
from basilisk_tools.verification import (
    DEFAULT_VERIFICATION_DIRECTORY,
    DEFAULT_VERIFICATION_TIMEOUT_SECONDS,
    verify_target,
)

app = typer.Typer(
    add_completion=False,
    help="Inspect, run, and verify AVS Basilisk simulations.",
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show the installed version and exit."),
    ] = False,
) -> None:
    """Inspect, run, and verify AVS Basilisk simulations."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo("Run 'bsk --help' to get started.")


def _render_dependency_table(title: str, dependencies: list[dict[str, object]]) -> None:
    table = Table(title=title)
    table.add_column("Dependency")
    table.add_column("Installed")
    table.add_column("Version")
    for dependency in dependencies:
        table.add_row(
            str(dependency["name"]),
            "yes" if dependency["installed"] else "no",
            str(dependency["version"] or "—"),
        )
    console.print(table)


@app.command()
def doctor(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
) -> None:
    """Check the Python and Basilisk environment."""
    report = collect_doctor_report()
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        state = "ready" if report["ok"] else "not ready"
        console.print(f"Basilisk Tools environment: {state}")
        python = report["python"]
        basilisk = report["basilisk"]
        tools = report["basilisk_tools"]
        console.print(f"Python: {python['version']} ({python['executable']})")
        console.print(f"Basilisk: {basilisk['version'] or 'not installed'}")
        console.print(f"Basilisk Tools: {tools['version']}")
        _render_dependency_table(
            "Required dependencies", report["required_dependencies"]
        )
        _render_dependency_table(
            "Optional development dependencies", report["optional_dependencies"]
        )
        for message in report["errors"]:
            console.print(f"Error: {message}")

    if not report["ok"]:
        raise typer.Exit(code=1)


def _run_exit_code(result: RunResult) -> int:
    if result.status == RunStatus.SUCCESS:
        return 0
    if result.status == RunStatus.TIMEOUT:
        return 124
    if result.status == RunStatus.INTERRUPTED:
        return 130
    return result.exit_code if result.exit_code and result.exit_code > 0 else 1


@app.command("run")
def run_command(
    scenario: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Trusted Python scenario to execute.",
        ),
    ],
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            min=0.01,
            help="Maximum execution time in seconds.",
        ),
    ] = DEFAULT_TIMEOUT_SECONDS,
    runs_dir: Annotated[
        Path,
        typer.Option(
            "--runs-dir",
            file_okay=False,
            help="Directory in which run artifacts are stored.",
        ),
    ] = DEFAULT_RUNS_DIRECTORY,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
) -> None:
    """Execute a trusted Python scenario in an isolated child process."""
    result = run_scenario(
        scenario,
        runs_directory=runs_dir,
        timeout_seconds=timeout,
    )
    if json_output:
        typer.echo(result.to_json())
    else:
        console.print(f"Run {result.run_id}: {result.status.value}")
        console.print(f"Elapsed: {result.elapsed_seconds:.3f} s")
        console.print(f"Artifacts: {result.artifacts['run_directory']}")
        if result.error:
            console.print(f"Error: {result.error.type}: {result.error.message}")

    exit_code = _run_exit_code(result)
    if exit_code:
        raise typer.Exit(code=exit_code)


def _tool_result_exit_code(payload: dict[str, object]) -> int:
    if payload.get("error"):
        return 1
    if not payload.get("supported", True):
        return 2
    if "passed" in payload and not payload["passed"]:
        return 3
    return 0


@app.command("inspect")
def inspect_command(
    scenario: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Instrumented Python scenario to inspect.",
        ),
    ],
    timeout: Annotated[
        float,
        typer.Option("--timeout", min=0.01, help="Inspection timeout in seconds."),
    ] = DEFAULT_INSPECTION_TIMEOUT_SECONDS,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
) -> None:
    """Inspect configured Basilisk structure without running the simulation."""
    report = inspect_scenario(scenario, timeout_seconds=timeout)
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    elif report.get("error"):
        error = report["error"]
        console.print(f"Inspection error: {error['type']}: {error['message']}")
    elif not report.get("supported"):
        console.print(f"Inspection unsupported: {report['reason']}")
    else:
        console.print(f"Scenario: {report['scenario']}")
        for case in report["cases"]:
            runtime = case["runtime"]
            console.print(f"Case: {case['name']}")
            if not runtime["supported"]:
                console.print(f"  Runtime inspection unavailable: {runtime['reason']}")
                continue
            table = Table("Order", "Process", "Task", "Period [s]", "Module")
            for module in runtime["modules"]:
                table.add_row(
                    str(module["execution_index"]),
                    str(module["process"]),
                    str(module["task"]),
                    str(module["task_period_s"]),
                    str(module["tag"]),
                )
            console.print(table)
            console.print(
                f"  Message connections: {len(runtime['message_connections'])}; "
                f"declared telemetry: {len(case['telemetry'])}"
            )

    exit_code = _tool_result_exit_code(report)
    if exit_code:
        raise typer.Exit(code=exit_code)


@app.command("verify")
def verify_command(
    target: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            resolve_path=True,
            help="Instrumented scenario, run directory, or result JSON.",
        ),
    ],
    timeout: Annotated[
        float,
        typer.Option("--timeout", min=0.01, help="Verification timeout in seconds."),
    ] = DEFAULT_VERIFICATION_TIMEOUT_SECONDS,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            file_okay=False,
            help="Directory for new verification executions.",
        ),
    ] = DEFAULT_VERIFICATION_DIRECTORY,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
) -> None:
    """Run declared checks or read them from an existing run."""
    try:
        report = verify_target(
            target,
            verification_directory=output_dir,
            timeout_seconds=timeout,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report = {
            "schema_version": 1,
            "supported": False,
            "scenario_path": str(target),
            "reason": str(error),
            "error": None,
        }

    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    elif report.get("error"):
        error = report["error"]
        console.print(f"Verification error: {error['type']}: {error['message']}")
    elif not report.get("supported", True):
        console.print(f"Verification unsupported: {report['reason']}")
    else:
        state = "PASS" if report["passed"] else "FAIL"
        console.print(f"Verification: {state} ({report['scenario']})")
        table = Table("Check", "Status", "Actual", "Expected", "Tolerance", "Units")
        for check in report["checks"]:
            table.add_row(
                str(check["name"]),
                "PASS" if check["passed"] else "FAIL",
                str(check["actual"]),
                str(check["expected"]),
                str(check["tolerance"]),
                str(check["units"] or "—"),
            )
        console.print(table)
        if report.get("artifacts", {}).get("verification"):
            console.print(f"Report: {report['artifacts']['verification']}")

    exit_code = _tool_result_exit_code(report)
    if exit_code:
        raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
