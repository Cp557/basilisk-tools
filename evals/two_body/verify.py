"""Verifier entry point for the two-body creation case."""

from pathlib import Path

from evals.verification import case_main

if __name__ == "__main__":
    raise SystemExit(case_main(Path(__file__).parent))
