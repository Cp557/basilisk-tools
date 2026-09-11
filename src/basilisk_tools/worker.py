"""Child-process entry point for executing trusted Python scenarios."""

import argparse
import json
import runpy
import sys
import traceback
from pathlib import Path
from typing import Any

from basilisk_tools.results import SCHEMA_VERSION


def _write_outcome(path: Path, *, exit_code: int, error: dict[str, str] | None) -> None:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "exit_code": exit_code,
        "error": error,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def execute_scenario(scenario_path: Path, outcome_path: Path) -> int:
    """Execute a scenario with normal script globals and record its outcome."""
    sys.argv = [str(scenario_path)]
    sys.path[0] = str(scenario_path.parent)

    try:
        runpy.run_path(str(scenario_path), run_name="__main__")
    except SystemExit as error:
        if error.code is None:
            exit_code = 0
        elif isinstance(error.code, int):
            exit_code = error.code
        else:
            exit_code = 1
            print(error.code, file=sys.stderr)

        summary = None
        if exit_code != 0:
            summary = {"type": "SystemExit", "message": str(error.code)}
        _write_outcome(outcome_path, exit_code=exit_code, error=summary)
        return exit_code
    except BaseException as error:
        traceback.print_exception(error, file=sys.stderr)
        _write_outcome(
            outcome_path,
            exit_code=1,
            error={"type": type(error).__name__, "message": str(error)},
        )
        return 1

    _write_outcome(outcome_path, exit_code=0, error=None)
    return 0


def main() -> int:
    """Parse worker-only arguments and execute the requested scenario."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--outcome", type=Path, required=True)
    parser.add_argument("scenario", type=Path)
    arguments = parser.parse_args()
    return execute_scenario(arguments.scenario, arguments.outcome)


if __name__ == "__main__":
    raise SystemExit(main())
