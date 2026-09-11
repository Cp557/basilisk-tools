"""Child-process worker for Basilisk-aware inspection and verification."""

from __future__ import annotations

import argparse
import json
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

from basilisk_tools.inspection import inspect_simulation
from basilisk_tools.instrumentation import (
    declares_contract,
    error_payload,
    load_contract,
    unsupported_payload,
)
from basilisk_tools.results import SCHEMA_VERSION


def _inspect(path: Path) -> dict[str, Any]:
    if not declares_contract(path):
        return unsupported_payload(
            path,
            "Scenario does not declare the basilisk_tools_scenario contract.",
        )

    contract = load_contract(path)
    cases = []
    for case in contract.build_cases():
        runtime = inspect_simulation(case.simulation)
        cases.append(
            {
                "name": case.name,
                "metadata": case.metadata,
                "runtime": runtime,
                "telemetry": [asdict(item) for item in case.telemetry],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "supported": True,
        "scenario_path": str(path),
        "scenario": contract.name,
        "description": contract.description,
        "cases": cases,
        "limitations": [
            "Telemetry units and frames are declared by the scenario contract.",
            "Runtime structure is reported before simulation initialization.",
        ],
        "error": None,
    }


def execute(operation: str, path: Path, output_dir: Path | None) -> dict[str, Any]:
    """Execute one Basilisk-aware operation and always return JSON-safe data."""
    path = path.resolve(strict=True)
    try:
        if operation == "inspect":
            return _inspect(path)
        if operation == "verify":
            if not declares_contract(path):
                return unsupported_payload(
                    path,
                    "Scenario does not declare the basilisk_tools_scenario contract.",
                )
            if output_dir is None:
                raise ValueError("Verification requires an output directory.")
            contract = load_contract(path)
            report = contract.verify(output_dir)
            return {
                "supported": True,
                "scenario_path": str(path),
                "error": None,
                **report.to_dict(),
            }
        raise ValueError(f"Unsupported worker operation: {operation}")
    except BaseException as error:
        traceback.print_exception(error)
        return error_payload(path, error)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("operation", choices=("inspect", "verify"))
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("scenario", type=Path)
    arguments = parser.parse_args()
    payload = execute(arguments.operation, arguments.scenario, arguments.output_dir)
    arguments.response.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if payload.get("error"):
        return 1
    if not payload.get("supported", False):
        return 2
    if arguments.operation == "verify" and not payload.get("passed", False):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
