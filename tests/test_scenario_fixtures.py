import subprocess
import sys
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scenarios"


def test_success_scenario_fixture() -> None:
    completed = subprocess.run(
        [sys.executable, str(FIXTURE_DIR / "success.py")],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == "scenario completed"
    assert completed.stderr.strip() == "scenario diagnostic"


def test_failure_scenario_fixture() -> None:
    completed = subprocess.run(
        [sys.executable, str(FIXTURE_DIR / "failure.py")],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode != 0
    assert "intentional scenario failure" in completed.stderr
