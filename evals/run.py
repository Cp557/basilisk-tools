"""Prepare and score reproducible Basilisk agent evaluations."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from basilisk_tools.results import SCHEMA_VERSION

EVALS_DIRECTORY = Path(__file__).resolve().parent
RESULTS_DIRECTORY = EVALS_DIRECTORY / "results"
CASES = ("two_body", "add_j2", "fix_units", "fix_telemetry")


def prepare_case(case: str, workspace: Path) -> None:
    """Copy a case's frozen starting files into a new workspace."""
    if workspace.exists():
        raise FileExistsError(f"Workspace already exists: {workspace}")
    shutil.copytree(EVALS_DIRECTORY / case / "starting_files", workspace)


def _result_identifier(case: str, agent: str, condition: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    safe_agent = "".join(
        character if character.isalnum() else "-" for character in agent
    )
    return f"{timestamp}-{case}-{safe_agent}-{condition}-{uuid.uuid4().hex[:8]}"


def score_case(arguments: argparse.Namespace) -> int:
    """Run a case verifier and record experiment metadata without guessing it."""
    result_directory = arguments.results_dir / _result_identifier(
        arguments.case, arguments.agent, arguments.condition
    )
    raw_directory = result_directory / "raw"
    result_directory.mkdir(parents=True)
    submission_snapshot = result_directory / "submission"
    shutil.copytree(
        arguments.submission.resolve(),
        submission_snapshot,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", ".bsk", "__pycache__", "*.pyc", "artifacts"
        ),
    )
    command = [
        sys.executable,
        "-m",
        f"evals.{arguments.case}.verify",
        str(arguments.submission.resolve()),
        "--output-dir",
        str(raw_directory),
    ]
    completed = subprocess.run(
        command,
        cwd=EVALS_DIRECTORY.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    (result_directory / "verifier-stdout.log").write_text(
        completed.stdout, encoding="utf-8"
    )
    (result_directory / "verifier-stderr.log").write_text(
        completed.stderr, encoding="utf-8"
    )
    verification_path = raw_directory / "verification.json"
    verification = (
        json.loads(verification_path.read_text(encoding="utf-8"))
        if verification_path.is_file()
        else {
            "schema_version": SCHEMA_VERSION,
            "passed": False,
            "checks": [],
            "error": "Verifier did not produce verification.json.",
        }
    )
    response_artifact = None
    if arguments.response:
        response_path = result_directory / "agent-response.md"
        shutil.copy2(arguments.response, response_path)
        response_artifact = str(response_path.resolve())

    explanation_path = submission_snapshot / "explanation.md"
    explanation_artifact = (
        str(explanation_path.resolve()) if explanation_path.is_file() else None
    )

    result = {
        "schema_version": SCHEMA_VERSION,
        "case": arguments.case,
        "agent": arguments.agent,
        "condition": arguments.condition,
        "automated_pass": bool(verification.get("passed")),
        "task_elapsed_seconds": arguments.task_seconds,
        "failed_simulation_attempts": arguments.failed_attempts,
        "human_interventions": arguments.human_interventions,
        "technical_explanation_score": arguments.explanation_score,
        "token_usage": {
            "input": arguments.input_tokens,
            "output": arguments.output_tokens,
        },
        "response_artifact": response_artifact,
        "explanation_artifact": explanation_artifact,
        "submission_artifact": str(submission_snapshot.resolve()),
        "verification": verification,
    }
    result_path = result_directory / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(result_path)
    return 0 if result["automated_pass"] else 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="Create a fresh case workspace.")
    prepare.add_argument("case", choices=CASES)
    prepare.add_argument("workspace", type=Path)

    score = commands.add_parser("score", help="Verify and record one agent result.")
    score.add_argument("case", choices=CASES)
    score.add_argument("submission", type=Path)
    score.add_argument("--agent", required=True)
    score.add_argument("--condition", choices=("baseline", "skill"), required=True)
    score.add_argument("--results-dir", type=Path, default=RESULTS_DIRECTORY)
    score.add_argument("--task-seconds", type=float)
    score.add_argument("--failed-attempts", type=int, default=0)
    score.add_argument("--human-interventions", type=int, default=0)
    score.add_argument("--explanation-score", type=int, choices=(0, 1, 2))
    score.add_argument("--input-tokens", type=int)
    score.add_argument("--output-tokens", type=int)
    score.add_argument("--response", type=Path)
    return parser


def main() -> int:
    """Dispatch the evaluation harness command."""
    arguments = _parser().parse_args()
    if arguments.command == "prepare":
        prepare_case(arguments.case, arguments.workspace.resolve())
        print(arguments.workspace.resolve())
        return 0
    return score_case(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
