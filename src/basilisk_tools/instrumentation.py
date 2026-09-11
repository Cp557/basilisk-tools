"""Small optional contract for inspectable and verifiable scenarios."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

from basilisk_tools.results import SCHEMA_VERSION, ErrorSummary

CONTRACT_FACTORY_NAME = "basilisk_tools_scenario"


@dataclass(frozen=True)
class TelemetrySpec:
    """Explicit telemetry metadata that Basilisk cannot infer reliably."""

    name: str
    source_message: str
    fields: tuple[str, ...]
    units: dict[str, str]
    sample_interval_s: float
    frame: str | None = None


@dataclass(frozen=True)
class ScenarioCase:
    """One configured Basilisk simulation exposed before execution."""

    name: str
    simulation: Any
    telemetry: tuple[TelemetrySpec, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationCheck:
    """One deterministic check declared by an instrumented scenario."""

    name: str
    passed: bool
    actual: Any
    expected: Any
    tolerance: float | None
    units: str | None


@dataclass(frozen=True)
class VerificationReport:
    """Normalized semantic verification result."""

    scenario: str
    passed: bool
    checks: tuple[VerificationCheck, ...]
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True)
class InstrumentedScenario:
    """Entry point shared by inspection and verification workers."""

    name: str
    description: str
    build_cases: Callable[[], tuple[ScenarioCase, ...]]
    verify: Callable[[Path], VerificationReport]


def declares_contract(path: Path) -> bool:
    """Check for a top-level contract factory without importing the scenario."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == CONTRACT_FACTORY_NAME
        for node in tree.body
    )


def _load_module(path: Path) -> ModuleType:
    module_name = f"_basilisk_tools_scenario_{path.stem}"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise ImportError(f"Cannot load scenario module from {path}")

    module = importlib.util.module_from_spec(specification)
    original_path = sys.path.copy()
    sys.path.insert(0, str(path.parent))
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.path[:] = original_path
    return module


def load_contract(path: Path) -> InstrumentedScenario:
    """Load and validate the declared scenario contract."""
    module = _load_module(path)
    factory = getattr(module, CONTRACT_FACTORY_NAME, None)
    if not callable(factory):
        raise TypeError(f"{CONTRACT_FACTORY_NAME} must be callable")
    contract = factory()
    if not isinstance(contract, InstrumentedScenario):
        raise TypeError(f"{CONTRACT_FACTORY_NAME} must return InstrumentedScenario")
    return contract


def unsupported_payload(path: Path, reason: str) -> dict[str, Any]:
    """Return an honest unsupported result shared by both tools."""
    return {
        "schema_version": SCHEMA_VERSION,
        "supported": False,
        "scenario_path": str(path),
        "reason": reason,
        "error": None,
    }


def error_payload(path: Path, error: BaseException) -> dict[str, Any]:
    """Return a concise structured tool failure."""
    return {
        "schema_version": SCHEMA_VERSION,
        "supported": True,
        "scenario_path": str(path),
        "error": asdict(ErrorSummary(type=type(error).__name__, message=str(error))),
    }
